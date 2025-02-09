import os
from typing import Any, BinaryIO

from google.cloud import storage  # type: ignore

from src.logger import logger
from src.utils import get_now

# 環境変数から GCP プロジェクトとバケット名を取得
gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
if os.getenv("USE_FIREBASE_EMULATOR") == "true":
    # Firebase のデフォルトバケット名規則に従う
    storage_bucket = f"{gcp_project}.appspot.com"
else:
    storage_bucket = os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET", "")


# プロジェクトが設定されている場合は project 引数を渡してクライアントを生成
storage_client = storage.Client(project=gcp_project)

# GCS上での論理ディレクトリ構造（リーディングスラッシュは含めない）
PRIVATE_DIR = "private"
PUBLIC_DIR = "public"
# private 以下（アクセス禁止：サーバー内でのみ利用する想定）
RSS_RAW_DIR = f"{PRIVATE_DIR}/rss"
OAI_PMH_RAW_DIR = f"{PRIVATE_DIR}/oai_pmh"
MASTERDATA_DIR = f"{PRIVATE_DIR}/masterdata"
# public 以下（認証済みユーザーに read 許可）
RADIO_SHOW_AUDIO_DIR = f"{PUBLIC_DIR}/radio_show_audio"
RADIO_SHOW_SCRIPT_DIR = f"{PUBLIC_DIR}/radio_show_script"


def _get_bucket() -> storage.Bucket:
    """GCSのバケットを取得する。"""
    # 1つの bucket のみでの運用を想定（user_project の指定は必要に応じて）
    bucket = storage_client.bucket(storage_bucket, user_project=gcp_project)
    logger.info(f"Get bucket: {bucket.name}")
    return bucket


def upload_blob(
    blob_path: str,
    file: BinaryIO,
    metadata: dict[str, Any],
    content_type: str,
    acl: str | None = None,
) -> str:
    """
    共通のアップロード処理。
    :param blob_path: GCS上のオブジェクトパス（例: "public/radio_show_audio/xxxx.mp3"）
    :param file: アップロードするファイルオブジェクト
    :param metadata: カスタムメタデータ
    :param content_type: MIME タイプ
    :param acl: 必要に応じたアクセスコントロール（例: "publicRead"）
    :return: アップロードしたオブジェクトの公開 URL
    """
    bucket = _get_bucket()
    blob = bucket.blob(blob_path)
    blob.metadata = metadata
    try:
        if acl:
            blob.upload_from_file(file, content_type=content_type, predefined_acl=acl)
        else:
            blob.upload_from_file(file, content_type=content_type)
    except Exception:
        logger.error(f"Failed to upload file to GCS: {blob_path}", exc_info=True)
        raise
    return blob.public_url


def put_tts_audio_file(signature: str, file: BinaryIO) -> str:
    """
    TTS後の音声ファイルを GCS にアップロードし、公開 URL を返す。
    キャッシュの有効期限は 7 日間。
    アップロード先: public/radio_show_audio/<signature>.mp3
    """
    blob_path = f"{RADIO_SHOW_AUDIO_DIR}/{signature}.mp3"
    metadata = {
        "Cache-Control": "public, max-age=604800",  # 7日間
        "content-type": "audio/mpeg",  # ※ メタデータとしての指定は任意
        "custom_time": get_now().isoformat(),
    }
    return upload_blob(
        blob_path, file, metadata, content_type="audio/mpeg", acl="publicRead"
    )


def put_combined_json_file(signature: str, file: BinaryIO) -> str:
    """
    Masterdata ファイル (JSON) を GCS にアップロードし、公開 URL を返す。
    キャッシュの有効期限は 5 分間。
    アップロード先: private/masterdata/<signature>.json
    """
    blob_path = f"{MASTERDATA_DIR}/{signature}.json"
    metadata = {
        "Cache-Control": "public, max-age=300",  # 5分間
        "content-type": "application/json; charset=utf-8",
        "custom_time": get_now().isoformat(),
    }
    return upload_blob(blob_path, file, metadata, content_type="application/json")


def put_rss_xml_file(signature: str, file: BinaryIO) -> str:
    """
    RSS XML ファイルを GCS にアップロードし、公開 URL を返す。
    キャッシュの有効期限は 5 分間。
    アップロード先: private/rss/<signature>.xml
    """
    blob_path = f"{RSS_RAW_DIR}/{signature}.xml"
    metadata = {
        "Cache-Control": "public, max-age=300",  # 5分間
        "content-type": "application/xml; charset=utf-8",
        "custom_time": get_now().isoformat(),
    }
    return upload_blob(blob_path, file, metadata, content_type="application/xml")


def put_oai_pmh_json_file(signature: str, file: BinaryIO) -> str:
    """
    OAI-PMH 用の JSON ファイルを GCS にアップロードし、公開 URL を返す。
    キャッシュの有効期限は 5 分間。
    アップロード先: private/oai_pmh/<signature>.json
    """
    blob_path = f"{OAI_PMH_RAW_DIR}/{signature}.json"
    metadata = {
        "Cache-Control": "public, max-age=300",  # 5分間
        "content-type": "application/json; charset=utf-8",
        "custom_time": get_now().isoformat(),
    }
    return upload_blob(blob_path, file, metadata, content_type="application/json")
