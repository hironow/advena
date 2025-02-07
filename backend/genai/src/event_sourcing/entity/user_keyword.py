from datetime import datetime
from re import U
from typing import Any, Callable

from google.api_core.exceptions import GoogleAPICallError, NotFound
from google.cloud.firestore import (
    DocumentReference,
    DocumentSnapshot,
    Transaction,
    transactional,
)
from pydantic import BaseModel

from src.database.firestore import db
from src.event_sourcing.entity.user import User, UserId
from src.logger import logger


class KeywordId(BaseModel):
    id: str
    user_id: str  # 親ユーザーのID（必ず設定されることを前提）


# ---------------------------------------------------------------------------
# エンティティ（Keyword）の定義
# ---------------------------------------------------------------------------
class Keyword(KeywordId):
    """
    Firestore の users/{userId}/keywords コレクションのドキュメントを表現するエンティティ。
    ※ __current_version__ は最新のスキーマバージョンを表す。
    """

    __collection__ = "keywords"  # 子コレクション名。親ユーザーの下に配置される
    __current_version__ = (
        1  # 今回は1を最新とする。必要に応じてマイグレーション関数を追加する
    )

    version: int
    created_at: datetime
    updated_at: datetime | None = None

    text: str


# ---------------------------------------------------------------------------
# 各バージョン間のマイグレーション処理
# ---------------------------------------------------------------------------
def keyword_migrate_from_0_to_1(doc: dict[str, Any]) -> dict[str, Any]:
    """
    バージョン 0 → 1 のマイグレーション:
      - updated_at を補完（なければ None）
      - version を 1 にセットする。
    ※ クライアントが最低限の情報のみを保存した場合（version 未設定）を想定
    """
    doc.setdefault("updated_at", None)
    doc["version"] = 1
    return doc


# バージョンごとのマイグレーション関数の登録
MIGRATIONS: dict[int, Callable[[dict[str, Any]], dict[str, Any]]] = {
    0: keyword_migrate_from_0_to_1,
}


# ---------------------------------------------------------------------------
# Firestore 更新をトランザクションで行うためのヘルパー
# ---------------------------------------------------------------------------
@transactional
def update_in_transaction(
    transaction: Transaction, doc_ref: DocumentReference, new_data: dict[str, Any]
) -> None:
    """
    トランザクション内で Keyword ドキュメントを更新する。
    現在のドキュメント内容と new_data が異なる場合に更新を実施する。
    """
    snapshot: DocumentSnapshot = doc_ref.get(transaction=transaction)
    current_data: dict[str, Any] = snapshot.to_dict() or {}
    if current_data != new_data:
        transaction.update(doc_ref, new_data)
        logger.info(
            f"Keyword document {doc_ref.id} updated: {current_data} -> {new_data}."
        )


def update(user: UserId, keyword: Keyword) -> None:
    """
    親ユーザーを第一引数に取り、対応するキーワードドキュメントを全更新する。
    ※ トランザクションを用いて、同時更新時の競合リスクを低減する。
    """
    try:
        # パスは: users/{user.id}/keywords/{keyword.id}
        doc_ref: DocumentReference = (
            db.collection(User.__collection__)
            .document(user.id)
            .collection(Keyword.__collection__)
            .document(keyword.id)
        )
        transaction: Transaction = db.transaction()
        update_in_transaction(transaction, doc_ref, keyword.model_dump())
    except GoogleAPICallError as e:
        logger.error(f"Error updating keyword {keyword.id} for user {user.id}: {e}")
        raise


# ---------------------------------------------------------------------------
# マイグレーション処理
# ---------------------------------------------------------------------------
def migrate(doc: DocumentSnapshot, auto_migrate: bool = True) -> dict[str, Any]:
    """
    Firestore のキーワードドキュメントのスキーマバージョンを確認し、必要に応じてマイグレーションを実行する。
    auto_migrate が True の場合、更新内容を Firestore に反映する。
    """
    # Firestore のドキュメントをミューテーブルな辞書に変換
    doc_dict: dict[str, Any] = dict(doc.to_dict() or {})
    if "version" not in doc_dict:
        doc_dict["version"] = 0
    current_version: int = doc_dict["version"]

    migration_applied: bool = False
    while current_version < Keyword.__current_version__:
        migration_func = MIGRATIONS.get(current_version)
        if migration_func is None:
            logger.error(
                f"No migration function defined for Keyword version {current_version}."
            )
            break
        try:
            new_doc = migration_func(doc_dict)
            if new_doc.get("version") == current_version:
                logger.error(
                    f"Migration function for Keyword version {current_version} did not update the version number."
                )
                break
            migration_applied = True
            current_version = new_doc["version"]
            doc_dict = new_doc
        except Exception as e:
            logger.error(
                f"Error during Keyword migration from version {current_version}: {e}"
            )
            break

    if auto_migrate and migration_applied:
        try:
            # 更新対象はこのキーワードドキュメント自身
            doc_ref: DocumentReference = doc.reference
            transaction: Transaction = db.transaction()
            update_in_transaction(transaction, doc_ref, doc_dict)
            logger.info(
                f"Auto-migrated Keyword document {doc.id} to version {doc_dict.get('version')}."
            )
        except GoogleAPICallError as e:
            logger.error(f"Failed to auto-migrate Keyword document {doc.id}: {e}")

    return doc_dict


# ---------------------------------------------------------------------------
# ドキュメント取得用関数
# ---------------------------------------------------------------------------
def get(user: UserId, keyword_id: str) -> Keyword | None:
    """
    親ユーザー（user）およびキーワードID に基づいてキーワードドキュメントを取得し、
    マイグレーションを適用した上で Keyword エンティティとして返す。
    """
    try:
        doc_ref: DocumentReference = (
            db.collection(User.__collection__)
            .document(user.id)
            .collection(Keyword.__collection__)
            .document(keyword_id)
        )
        doc: DocumentSnapshot = doc_ref.get()
    except NotFound:
        logger.warning(f"Keyword document {keyword_id} not found for user {user.id}.")
        return None

    if not doc.exists:
        return None

    doc_dict = migrate(doc)
    try:
        return Keyword(**doc_dict)
    except Exception as e:
        logger.error(f"Error parsing Keyword document {doc.id}: {e}")
        raise


def get_by_field(user: UserId, field: str, value: Any) -> Keyword | None:
    """
    親ユーザー（user）の keywords サブコレクションに対して、指定フィールド (例: 'text')
    の値で検索し、単一の Keyword エンティティを返す。
    重複が見つかった場合は None を返すので、必要に応じた重複対応を実装してください。
    """
    try:
        docs = list(
            db.collection(User.__collection__)
            .document(user.id)
            .collection(Keyword.__collection__)
            .where(field, "==", value)
            .stream()
        )
    except GoogleAPICallError as e:
        logger.error(
            f"Error querying keyword for field {field} with value {value} for user {user.id}: {e}"
        )
        return None

    if len(docs) == 1:
        doc_dict = migrate(docs[0])
        try:
            return Keyword(**doc_dict)
        except Exception as e:
            logger.error(f"Error parsing Keyword document {docs[0].id}: {e}")
            raise
    elif len(docs) > 1:
        logger.error(
            f"Multiple Keyword documents found for field {field} with value {value} for user {user.id}."
        )
    return None
