from datetime import datetime
from typing import Any, Callable, Literal, Optional

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


# RadioShowId は id のみを持つモデル
class RadioShowId(BaseModel):
    id: str


# ---------------------------------------------------------------------------
# エンティティ（RadioShow）の定義
# ---------------------------------------------------------------------------
class RadioShow(RadioShowId):
    """
    Firestore の radio_shows コレクションのドキュメントを表現するエンティティ。
    ※ __current_version__ は最新のスキーマバージョンを表す。
    """

    __collection__ = "radio_shows"  # 作成後は変更不可
    __current_version__ = 2

    version: int
    created_at: datetime
    updated_at: datetime | None = None

    # ラジオショー固有のフィールド例
    radio_show_id: str  # ドキュメントIDと同一でもよい
    title: str
    host: str
    # ここでは、クライアントは "draft" 状態で最低限の情報のみを登録すると仮定する
    status: Literal["draft"] | Literal["published"]
    # 追加オプションフィールド
    description: str | None = None


# ---------------------------------------------------------------------------
# 各バージョン間のマイグレーション処理
# ---------------------------------------------------------------------------
def radio_migrate_from_0_to_1(doc: dict[str, Any]) -> dict[str, Any]:
    """
    バージョン 0 → 1 のマイグレーション:
      - 必要なオプショナルフィールドに対して、デフォルト値を補完する。
      - status が "draft" なら "published" に変更する。
      - version を 1 にセットする。
    """
    if doc.get("status") == "draft":
        doc["status"] = "published"
    doc.setdefault("updated_at", None)
    doc.setdefault("description", "")
    doc["version"] = 1
    return doc


def radio_migrate_from_1_to_2(doc: dict[str, Any]) -> dict[str, Any]:
    """
    バージョン 1 → 2 のマイグレーション:
      - title に対して、存在しない場合は "Untitled Show" を設定（例）。
      - version を 2 にセットする。
    """
    doc.setdefault("title", "Untitled Show")
    doc["version"] = 2
    return doc


# バージョンごとのマイグレーション関数の登録
MIGRATIONS: dict[int, Callable[[dict[str, Any]], dict[str, Any]]] = {
    0: radio_migrate_from_0_to_1,
    1: radio_migrate_from_1_to_2,
}


# ---------------------------------------------------------------------------
# Firestore 更新をトランザクションで行うためのヘルパー
# ---------------------------------------------------------------------------
@transactional
def update_in_transaction(
    transaction: Transaction, doc_ref: DocumentReference, new_data: dict[str, Any]
) -> None:
    snapshot: DocumentSnapshot = doc_ref.get(transaction=transaction)
    current_data = snapshot.to_dict() or {}
    if current_data != new_data:
        transaction.update(doc_ref, new_data)
        logger.info(f"Document {doc_ref.id} updated: {current_data} -> {new_data}.")


def update(radio_show_id: str, radio_show: RadioShow) -> None:
    """
    ラジオショーを全更新する。
    ※トランザクションを用いて、同時更新時の競合リスクを低減する。
    """
    try:
        doc_ref: DocumentReference = db.collection(RadioShow.__collection__).document(
            radio_show_id
        )
        transaction: Transaction = db.transaction()
        update_in_transaction(transaction, doc_ref, radio_show.model_dump())
    except GoogleAPICallError as e:
        logger.error(f"Error updating radio show {radio_show_id}: {e}")
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

    migration_applied = False
    while current_version < RadioShow.__current_version__:
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

    if auto_migrate and migration_applied:
        try:
            doc_ref: DocumentReference = db.collection(
                RadioShow.__collection__
            ).document(doc.id)
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
def get(radio_show_id: str) -> RadioShow | None:
    """
    ラジオショーID に基づいてドキュメントを取得し、マイグレーションを適用した上で RadioShow エンティティとして返す。
    """
    try:
        doc_ref: DocumentReference = db.collection(RadioShow.__collection__).document(
            radio_show_id
        )
        doc = doc_ref.get()
    except NotFound:
        logger.warning(f"Radio show document {radio_show_id} not found.")
        return None

    if not doc.exists:
        return None

    doc_dict = migrate(doc)
    try:
        return RadioShow(**doc_dict)
    except Exception as e:
        logger.error(f"Error parsing radio show document {doc.id}: {e}")
        raise


def get_by_field(field: str, value: Any) -> RadioShow | None:
    """
    指定フィールド (例: 'title' や 'host') による検索を行い、単一の RadioShow エンティティを返す。
    重複が見つかった場合は None を返すので、必要に応じた重複対応を実装してください。
    """
    try:
        docs = list(
            db.collection(RadioShow.__collection__).where(field, "==", value).stream()
        )
    except GoogleAPICallError as e:
        logger.error(f"Error querying {field} {value}: {e}")
        return None

    if len(docs) == 1:
        doc_dict = migrate(docs[0])
        try:
            return RadioShow(**doc_dict)
        except Exception as e:
            logger.error(f"Error parsing radio show document {docs[0].id}: {e}")
            raise
    elif len(docs) > 1:
        logger.error(f"Multiple documents found for {field} {value}.")
    return None
