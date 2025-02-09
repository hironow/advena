import io
import os
from datetime import datetime
from typing import Any, BinaryIO
from zoneinfo import ZoneInfo

from google.cloud import storage  # type: ignore

from src import blob
from src.logger import logger
from src.utils import get_diff_days, get_now

# 環境変数から GCP プロジェクトとバケット名を取得
gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
storage_bucket: str
if os.getenv("USE_FIREBASE_EMULATOR") == "true":
    # Firebase のデフォルトバケット名規則に従う
    storage_bucket = f"{gcp_project}.firebasestorage.app"
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

XML_LATEST_ALL_DIR_BASE = "latest_all"
XML_KEYWORD_DIR_BASE = "keyword"

ISBN_DIR = "isbn"
JP_E_CODE_DIR = "jp_e_code"


def _get_bucket() -> storage.Bucket:
    """GCSのバケットを取得する。"""
    # 1つの bucket のみでの運用を想定（user_project の指定は必要に応じて）
    logger.info(f"target bucket: {storage_bucket}")
    bucket = storage_client.bucket(bucket_name=storage_bucket, user_project=gcp_project)
    logger.info(f"Get bucket: {bucket.name}")
    return bucket


def _upload_blob_file(
    blob_path: str,
    file: BinaryIO,
    metadata: dict[str, Any],
    content_type: str,
    acl: str | None = None,
) -> storage.Blob:
    """ファイルを GCS にアップロードし、公開 URL を返す。"""
    bucket = _get_bucket()
    blob = bucket.blob(blob_path)
    blob.metadata = metadata

    logger.info(f"Uploading file to GCS: {blob_path}")
    logger.info(f"Metadata: {metadata}")
    try:
        if acl:
            blob.upload_from_file(file, content_type=content_type, predefined_acl=acl)
        else:
            blob.upload_from_file(file, content_type=content_type)
    except Exception:
        logger.error(f"Failed to upload file to GCS: {blob_path}", exc_info=True)
        raise
    return blob


def _upload_blob_string(
    blob_path: str,
    s: str,
    metadata: dict[str, Any],
    content_type: str,
    acl: str | None = None,
) -> storage.Blob:
    """文字列を GCS にアップロードし、公開 URL を返す。"""
    bucket = _get_bucket()
    blob = bucket.blob(blob_path)
    blob.metadata = metadata

    logger.info(f"Uploading file to GCS: {blob_path}")
    logger.info(f"Metadata: {metadata}")
    try:
        if acl:
            blob.upload_from_string(s, content_type=content_type, predefined_acl=acl)
        else:
            blob.upload_from_string(s, content_type=content_type)
    except Exception:
        logger.error(f"Failed to upload string to GCS: {blob_path}", exc_info=True)
        raise
    return blob


def put_tts_audio_file(signature: str, file: BinaryIO) -> storage.Blob:
    """
    TTS後の音声ファイルを GCS にアップロードし、公開 URL を返す。
    キャッシュの有効期限は 7 日間。
    アップロード先: public/radio_show_audio/<signature>.mp3
    """
    if signature == "":
        raise ValueError("signature should not be empty.")
    blob_path = f"{RADIO_SHOW_AUDIO_DIR}/{signature}.mp3"
    metadata = {
        "Cache-Control": "public, max-age=604800",  # 7日間
        "content-type": "audio/mpeg",  # ※ メタデータとしての指定は任意
        "custom_time": get_now().isoformat(),
    }
    # 先頭へ
    file.seek(0)
    return _upload_blob_file(
        blob_path, file, metadata, content_type="audio/mpeg", acl="publicRead"
    )


def put_rss_xml_file(
    last_build_date: datetime, prefix_dir: str, file: BinaryIO, suffix_dir: str = "non"
) -> storage.Blob:
    """
    RSS XML ファイルを GCS にアップロードし、公開 URL を返す。
    キャッシュの有効期限は 5 分間。
    アップロード先: private/rss/(latest_all|keyword_X)/<signature>.xml

    signature: ファイル名の接頭辞として利用する日時文字列 (JST)
    例: 20250209_000000_0900
    """
    if prefix_dir == "":
        raise ValueError("signature should not be empty.")
    last_build_date_w_tz = last_build_date
    if last_build_date_w_tz.tzinfo != ZoneInfo("Asia/Tokyo"):
        last_build_date_w_tz = last_build_date.astimezone(ZoneInfo("Asia/Tokyo"))

    signature = f"{last_build_date_w_tz.strftime('%Y%m%d_%H%M%S_0900')}"
    blob_path = f"{RSS_RAW_DIR}/{prefix_dir}_{suffix_dir}/{signature}.xml"
    metadata = {
        "Cache-Control": "public, max-age=300",  # 5分間
        "content-type": "application/xml; charset=utf-8",
        "custom_time": get_now().isoformat(),
    }
    # 先頭へ
    file.seek(0)
    return _upload_blob_file(blob_path, file, metadata, content_type="application/xml")


def put_oai_pmh_json(signature: str, prefix_dir: str, json_str: str) -> storage.Blob:
    """
    OAI-PMH 用の JSON ファイルを GCS にアップロードし、公開 URL を返す。
    キャッシュの有効期限は 5 分間。
    アップロード先: private/oai_pmh/(isbn|jp_e_code)/<signature>.json
    """
    if signature == "" or json_str == "" or prefix_dir == "":
        raise ValueError("signature should not be empty.")
    blob_path = f"{OAI_PMH_RAW_DIR}/{prefix_dir}/{signature}.json"
    metadata = {
        "Cache-Control": "public, max-age=300",  # 5分間
        "content-type": "application/json; charset=utf-8",
        "custom_time": get_now().isoformat(),
    }
    return _upload_blob_string(
        blob_path, json_str, metadata, content_type="application/json"
    )


def put_combined_json_file(signature: str, json_str: str) -> storage.Blob:
    """
    Masterdata ファイル (JSON) を GCS にアップロードし、公開 URL を返す。
    キャッシュの有効期限は 5 分間。
    アップロード先: private/masterdata/<signature>.json
    """
    if signature == "" or json_str == "":
        raise ValueError("signature should not be empty.")
    blob_path = f"{MASTERDATA_DIR}/{signature}.json"
    metadata = {
        "Cache-Control": "public, max-age=300",  # 5分間
        "content-type": "application/json; charset=utf-8",
        "custom_time": get_now().isoformat(),
    }
    return _upload_blob_string(
        blob_path, json_str, metadata, content_type="application/json"
    )


def get_closest_cached_rss_file(
    target_utc: datetime, prefix_dir: str, suffix_dir: str = "non"
) -> io.BytesIO | None:
    """指定日のキャッシュされた RSS ファイルを取得する。prefix_dir は private/rss 以下のディレクトリ名。"""
    if prefix_dir == "":
        raise ValueError("target_isbn and prefix_dir should not be empty.")
    if target_utc is None:
        raise ValueError("target_utc should not be None.")

    # タイムゾーンを UTC から JST に変換
    target_jst = target_utc.astimezone(ZoneInfo("Asia/Tokyo"))

    bucket = _get_bucket()
    prefix_base = f"{RSS_RAW_DIR}/{prefix_dir}_{suffix_dir}"
    # ソートはできないので、日までが同じものを全て取得してから、チェックする
    # ex: "private/rss/latest_all/20250209"
    search_prefix = prefix_base + "/" + target_jst.strftime("%Y%m%d")

    logger.info(f"searching for cached RSS files...: {search_prefix}")
    blobs: list[storage.Blob] = list(
        bucket.list_blobs(
            prefix=search_prefix,
            max_results=10,
        )
    )
    if not blobs:
        logger.info("No cached RSS files found.")
        return None

    # 同日の中で最も新しいファイルを有効なキャッシュとする
    newest_blob: storage.Blob | None = None
    for blob in blobs:
        logger.info(f"blob name: {blob.name}")
        if newest_blob is None:
            newest_blob = blob
        elif blob.time_created is not None and newest_blob.time_created is not None:
            if blob.time_created > newest_blob.time_created:
                newest_blob = blob

    if newest_blob is None:
        logger.info("No cached RSS files found.")
        return None

    logger.info(f"Found closest cached RSS file: {newest_blob.name}")

    bs = io.BytesIO()
    newest_blob.download_to_file(bs)
    # ファイルの先頭に戻す
    bs.seek(0)
    return bs


def get_closest_cached_oai_pmh_file(
    target_isbn: str, prefix_dir: str
) -> io.BytesIO | None:
    if target_isbn == "" or prefix_dir == "":
        raise ValueError("target_isbn and prefix_dir should not be empty.")

    bucket = _get_bucket()
    prefix_base = f"{OAI_PMH_RAW_DIR}/{prefix_dir}"
    # ソートはできないので、同じものを取得してから、作成日チェックして、7日以内のものを取得する
    # ex: "private/oai_pmh/isbn/9784621310328"
    search_prefix = prefix_base + "/" + target_isbn

    logger.info(f"searching for cached OAI-PMH files...: {search_prefix}")
    blobs: list[storage.Blob] = list(
        bucket.list_blobs(
            prefix=search_prefix,
            max_results=10,
        )
    )
    if not blobs:
        logger.info("No cached OAI-PMH files found.")
        return None

    # 7日以内を有効なキャッシュとする
    utcnow = get_now()
    newest_blob: storage.Blob | None = None
    for blob in blobs:
        logger.info(f"blob name: {blob.name}")
        if newest_blob is None:
            newest_blob = blob
        elif blob.time_created is not None and newest_blob.time_created is not None:
            if blob.time_created > newest_blob.time_created:
                newest_blob = blob
    if newest_blob is None:
        logger.info("No cached OAI-PMH files found.")
        return None

    if (
        newest_blob.time_created is not None
        and get_diff_days(utcnow, newest_blob.time_created) > 7
    ):
        logger.info("Cached OAI-PMH file is too old.")
        return None

    logger.info(f"Found closest cached OAI-PMH file: {newest_blob.name}")

    bs = io.BytesIO()
    newest_blob.download_to_file(bs)
    # ファイルの先頭に戻す
    bs.seek(0)
    return bs


def get_json_file(blob_path: str) -> str:
    """
    Masterdata ファイル (JSON) を GCS から取得する。
    URL は private/masterdata/<signature>.json とする。
    """
    if blob_path == "":
        raise ValueError("url should not be empty.")
    bucket = _get_bucket()
    blob = bucket.blob(blob_path)
    try:
        json_str = blob.download_as_string()
    except Exception:
        logger.error(f"Failed to download string from GCS: {blob_path}", exc_info=True)
        raise
    return json_str.decode("utf-8")
