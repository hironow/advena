import base64
import json
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

from src import utils
from src.database import cloudevents
from src.database.firestore import db, use_emulator
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
    __current_version__ = 1

    version: int
    created_at: datetime
    updated_at: datetime | None = None

    # ラジオショー固有のフィールド例
    status: Literal["creating"] | Literal["created"]
    # masterdataは非公開なので blob path で管理
    masterdata_blob_path: str
    # 過去日の指定をしたいときは datetime で作成時に指定する
    broadcasted_at: datetime | None = None
    # public url は公開されるのでそのまま保持
    audio_url: str | None = None
    script_url: str | None = None


# ---------------------------------------------------------------------------
# 各バージョン間のマイグレーション処理
# ---------------------------------------------------------------------------
def radio_migrate_from_0_to_1(doc: dict[str, Any]) -> dict[str, Any]:
    """
    バージョン 0 → 1 のマイグレーション:
      - version を 1 にセットする。
    """
    doc["version"] = 1
    return doc


# バージョンごとのマイグレーション関数の登録
MIGRATIONS: dict[int, Callable[[dict[str, Any]], dict[str, Any]]] = {
    0: radio_migrate_from_0_to_1,
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


def new(masterdata_blob_path: str, broadcasted_at: datetime | None) -> RadioShow:
    """
    新規ラジオショーを作成する。
    """
    radio_show_id = utils.new_id()
    radio_show = RadioShow(
        id=radio_show_id,
        version=RadioShow.__current_version__,
        created_at=utils.get_now(),
        status="creating",
        masterdata_blob_path=masterdata_blob_path,
        broadcasted_at=broadcasted_at,
    )
    try:
        doc_ref: DocumentReference = db.collection(RadioShow.__collection__).document(
            radio_show_id
        )
        doc_ref.set(radio_show.model_dump())
    except GoogleAPICallError as e:
        logger.error(f"Error creating radio show {radio_show_id}: {e}")
        raise e

    if use_emulator:
        data = {"id": radio_show_id}
        data_json = json.dumps(data)
        data_base64 = base64.b64encode(data_json.encode("utf-8")).decode("utf-8")
        event_body = cloudevents.create_cloud_event_body(
            RadioShow.__collection__,
            radio_show_id,
            data_base64,
        )
        cloudevents.send_cloud_event(
            cloudevents.EVENTARC_ENDPOINT_ADD_RADIO_SHOW, event_body
        )

    return radio_show


def update_audio_and_script_url(
    radio_show_id: str, audio_url: str, script_url: str
) -> None:
    """
    ラジオショーの audio_url を更新する。
    """
    now = utils.get_now()
    ref = db.collection(RadioShow.__collection__).document(radio_show_id)
    ref.update(
        {
            "audio_url": audio_url,
            "script_url": script_url,
            "status": "created",
            "updated_at": now,
        }
    )
