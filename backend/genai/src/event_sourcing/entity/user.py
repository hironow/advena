from datetime import datetime
from typing import Any, Callable, Literal

from google.api_core.exceptions import GoogleAPICallError, NotFound
from google.cloud.firestore import (
    DocumentReference,
    DocumentSnapshot,
    Transaction,
    transactional,
)
from pydantic import BaseModel

from src.database.firestore import db
from src.logger import logger


# UserId は id のみを持つモデル
class UserId(BaseModel):
    id: str


# ---------------------------------------------------------------------------
# エンティティ（User）の定義
# ---------------------------------------------------------------------------
class User(UserId):
    """
    Firestore の users コレクションのドキュメントを表現するエンティティ。
    ※ __current_version__ は最新のスキーマバージョンを表す。
    """

    __collection__ = "users"  # 作成後は変更不可
    __current_version__ = 2  # マイグレーションを追加するたびに更新する

    version: int
    created_at: datetime
    updated_at: datetime | None = None

    firebase_uid: str
    status: Literal["creating"] | Literal["created"]
    last_signed_in: datetime | None = None
    continuous_login_count: int = 0
    login_count: int = 0

    # 例: マイグレーションで追加されたフィールド（version 2 で追加した場合）
    name: str | None = None


# ---------------------------------------------------------------------------
# 各バージョン間のマイグレーション処理
# ---------------------------------------------------------------------------
def migrate_from_0_to_1(doc: dict[str, Any]) -> dict[str, Any]:
    """
    バージョン 0 → 1 のマイグレーション:
      - 必要なオプショナルフィールドに対して、デフォルト値を補完する。
      - status が "creating" なら "created" に変更する。
      - version を 1 にセットする。
    """
    # もし status が "creating" なら "created" に変換
    if doc.get("status") == "creating":
        doc["status"] = "created"
    # 必要なフィールドの補完
    doc.setdefault("updated_at", None)
    doc.setdefault("last_signed_in", None)
    doc.setdefault("continuous_login_count", 0)
    doc.setdefault("login_count", 0)
    # version をアップデート
    doc["version"] = 1
    return doc


def migrate_from_1_to_2(doc: dict[str, Any]) -> dict[str, Any]:
    """
    バージョン 1 → 2 のマイグレーション:
      - name フィールドを補完（なければデフォルト値 "Default Name" を設定）
      - version を 2 にセットする。
    """
    doc.setdefault("name", "Default Name")
    doc["version"] = 2
    return doc


# バージョンごとのマイグレーション関数の登録
MIGRATIONS: dict[int, Callable[[dict[str, Any]], dict[str, Any]]] = {
    0: migrate_from_0_to_1,
    1: migrate_from_1_to_2,
}


# ---------------------------------------------------------------------------
# Firestore 更新をトランザクションで行うためのヘルパー
# ---------------------------------------------------------------------------
@transactional
def update_in_transaction(
    transaction: Transaction, doc_ref: DocumentReference, new_data: dict[str, Any]
) -> None:
    """
    トランザクション内でドキュメントを更新する。
    ※現状のドキュメント内容と new_data が異なる場合に更新を実施する。
    """
    snapshot: DocumentSnapshot = doc_ref.get(transaction=transaction)
    current_data = snapshot.to_dict() or {}
    # 更新前後の差分がある場合は更新する
    if current_data != new_data:
        transaction.update(doc_ref, new_data)
        logger.info(f"Document {doc_ref.id} updated: {current_data} -> {new_data}.")


def update(user_id: str, user: User) -> None:
    """
    ユーザーを全更新する。
    ※トランザクションを用いて、同時更新時の競合リスクを低減。
    """
    try:
        doc_ref: DocumentReference = db.collection(User.__collection__).document(
            user_id
        )
        transaction: Transaction = db.transaction()
        update_in_transaction(transaction, doc_ref, user.model_dump())
    except GoogleAPICallError as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise


# ---------------------------------------------------------------------------
# マイグレーション処理
# ---------------------------------------------------------------------------
def migrate(doc: DocumentSnapshot, auto_migrate: bool = True) -> dict[str, Any]:
    # Firestore のドキュメントをミューテーブルな辞書に変換
    doc_dict: dict[str, Any] = dict(doc.to_dict() or {})
    # version フィールドがなければ 0 とする
    if "version" not in doc_dict:
        doc_dict["version"] = 0
    current_version = doc_dict["version"]

    # マイグレーション関数のチェーン
    migration_applied = False
    while current_version < User.__current_version__:
        migration_func = MIGRATIONS.get(current_version)
        if migration_func is None:
            logger.error(
                f"No migration function defined for version {current_version}."
            )
            break
        try:
            new_doc = migration_func(doc_dict)
            if new_doc.get("version") == current_version:
                logger.error(
                    f"Migration function for version {current_version} did not update the version number."
                )
                break
            migration_applied = True
            current_version = new_doc["version"]
            doc_dict = new_doc
        except Exception as e:
            logger.error(f"Error during migration from version {current_version}: {e}")
            break

    # 自動マイグレーションが必要なら Firestore 側も更新
    if auto_migrate and migration_applied:
        try:
            doc_ref: DocumentReference = db.collection(User.__collection__).document(
                doc.id
            )
            transaction: Transaction = db.transaction()
            update_in_transaction(transaction, doc_ref, doc_dict)
            logger.info(
                f"Auto-migrated document {doc.id} to version {doc_dict.get('version')}."
            )
        except GoogleAPICallError as e:
            logger.error(f"Failed to auto-migrate document {doc.id}: {e}")

    return doc_dict


# ---------------------------------------------------------------------------
# ドキュメント取得用関数
# ---------------------------------------------------------------------------
def get(user_id: str) -> User | None:
    """
    ユーザーID に基づいてドキュメントを取得し、マイグレーションを適用した上で User エンティティとして返す。
    """
    try:
        doc_ref: DocumentReference = db.collection(User.__collection__).document(
            user_id
        )
        doc = doc_ref.get()
    except NotFound:
        logger.warning(f"User document {user_id} not found.")
        return None

    if not doc.exists:
        return None

    doc_dict = migrate(doc)
    try:
        return User(**doc_dict)
    except Exception as e:
        logger.error(f"Error parsing user document {doc.id}: {e}")
        raise


def get_by_firebase_uid(firebase_uid: str) -> User | None:
    """
    firebase_uid でユーザーを検索する。
    重複が見つかった場合はエラーとなるため、必要に応じた対応を検討する。
    """
    try:
        docs = list(
            db.collection(User.__collection__)
            .where("firebase_uid", "==", firebase_uid)
            .stream()
        )
    except GoogleAPICallError as e:
        logger.error(f"Error querying firebase_uid {firebase_uid}: {e}")
        return None

    if len(docs) == 1:
        doc_dict = migrate(docs[0])
        try:
            return User(**doc_dict)
        except Exception as e:
            logger.error(f"Error parsing user document {docs[0].id}: {e}")
            raise
    elif len(docs) > 1:
        logger.error(f"Multiple documents found for firebase_uid {firebase_uid}.")
        # 必要に応じて重複時の処理（例: エラー通知や削除処理等）を実装
    return None
