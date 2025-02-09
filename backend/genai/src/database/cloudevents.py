import json
import os
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

from src.logger import logger

# Eventarc のエミュレータ用エンドポイント
EVENTARC_ENDPOINT_BASE = "http://localhost:8000"
EVENTARC_ENDPOINT_ADD_USER = f"{EVENTARC_ENDPOINT_BASE}/add_user"
EVENTARC_ENDPOINT_ADD_RADIO_SHOW = f"{EVENTARC_ENDPOINT_BASE}/add_radio_show"


def create_cloud_event_body(
    collection: str, doc_id: str, data_base64: str
) -> dict[str, Any]:
    """
    CloudEvent ボディを生成する関数

    :param collection: Firestore のコレクション名
    :param doc_id: ドキュメントの ID
    :param data_base64: Base64 エンコード済みのデータ(JSON文字列)
    :return: CloudEvent の辞書オブジェクト
    """
    # 環境変数からプロジェクトIDを取得（無い場合はデフォルト値を設定）
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    # ISO 8601 形式のUTC時刻（末尾に "Z" を付与）
    time_iso = datetime.now(UTC).isoformat() + "Z"

    return {
        "specversion": "1.0",
        "id": str(uuid.uuid4()),
        "source": f"//firestore.googleapis.com/projects/{project_id}/databases/(default)/documents",
        "type": "google.cloud.firestore.document.v1.created",
        "time": time_iso,
        "datacontenttype": "application/json",
        "subject": f"documents/{collection}/{doc_id}",
        # Python 側で参照するためのフィールドを追加
        "document": f"{collection}/{doc_id}",
        "data_base64": data_base64,
    }


def send_cloud_event(endpoint: str, event_body: dict[str, Any]) -> None:
    """
    CloudEvent を指定のエンドポイントへ POST する関数

    :param endpoint: 送信先の URL
    :param event_body: 送信する CloudEvent のボディ
    """
    try:
        logger.info(f"[COMMAND] Sending CloudEvent to {endpoint}")
        logger.info(f"[COMMAND] Event body: {json.dumps(event_body)}")

        headers = {"Content-Type": "application/cloudevents+json"}
        response = httpx.post(endpoint, headers=headers, json=event_body)

        if response.status_code < 300:
            logger.info("[INFO] CloudEvent sent successfully.")
        else:
            logger.error(
                f"[ERROR] Failed to send CloudEvent: {response.status_code} {response.reason_phrase}"
            )
    except Exception as e:
        logger.error(f"[ERROR] Exception while sending CloudEvent: {e}")
