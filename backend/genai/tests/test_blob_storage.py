import io
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from src.blob import storage as gcs_module


class FakeBlob:
    def __init__(self, name, time_created=None, content=None):
        self.name = name
        self.metadata = {}
        self.time_created = time_created
        self._content = content  # バイト列で保持

    def download_as_string(self):
        if self._content is None:
            raise Exception("No content")
        return self._content

    def download_to_file(self, file_obj: io.BytesIO):
        if self._content is None:
            raise Exception("No content")
        file_obj.write(self._content)

    def upload_from_string(self, s, content_type=None, predefined_acl=None):
        self._content = s.encode("utf-8")

    def upload_from_file(self, file, content_type=None, predefined_acl=None):
        file.seek(0)
        self._content = file.read()


class FakeBucket:
    def __init__(self):
        # 辞書形式で blob_path -> FakeBlob を保持
        self._blobs = {}

    def blob(self, blob_path: str) -> FakeBlob:
        if blob_path in self._blobs:
            return self._blobs[blob_path]
        else:
            new_blob = FakeBlob(blob_path)
            self._blobs[blob_path] = new_blob
            return new_blob

    def list_blobs(self, prefix: str, max_results=None):
        # prefix で始まる blob を抽出
        results = [
            blob for name, blob in self._blobs.items() if name.startswith(prefix)
        ]
        # time_created の古い順にソート（time_created が None の場合は datetime.min とみなす）
        results.sort(key=lambda b: b.time_created or datetime.min)
        if max_results:
            return results[:max_results]
        return results


@pytest.fixture
def fake_bucket(monkeypatch):
    """
    _get_bucket() を FakeBucket を返すように差し替える
    """
    bucket = FakeBucket()
    monkeypatch.setattr(gcs_module, "_get_bucket", lambda: bucket)
    return bucket


@pytest.fixture
def fixed_now():
    """固定の現在時刻 (UTC) を返す"""
    return datetime(2025, 2, 9, 10, 0, 0, tzinfo=ZoneInfo("UTC"))


def test_put_combined_json_file(fake_bucket, fixed_now, monkeypatch):
    # get_now() を固定時刻に差し替え
    monkeypatch.setattr(gcs_module, "get_now", lambda: fixed_now)
    signature = "test_signature"
    json_str = '{"key": "value"}'

    blob = gcs_module.put_combined_json_file(signature, json_str)
    expected_blob_path = f"{gcs_module.MASTERDATA_DIR}/{signature}.json"
    assert blob.name == expected_blob_path, "Blob のパスが正しく生成されている"
    # メタデータにキャッシュ設定等が含まれていることをチェック
    assert blob.metadata.get("Cache-Control") == "public, max-age=300"
    # アップロードしたコンテンツが正しく保存されている
    assert blob._content == json_str.encode("utf-8")


def test_get_json_file(fake_bucket):
    # テスト用の Blob を作成し、コンテンツを設定する
    blob_path = f"{gcs_module.MASTERDATA_DIR}/test_signature.json"
    test_content = '{"key": "value"}'
    bucket = fake_bucket  # FakeBucket インスタンス
    blob = bucket.blob(blob_path)
    blob._content = test_content.encode("utf-8")

    # get_json_file() を呼び出し、内容が正しく取得できるか確認
    result = gcs_module.get_json_file(blob_path)
    assert result == test_content, "取得した JSON の内容が一致する"


def test_put_tts_audio_file(fake_bucket):
    signature = "audio_test"
    file_content = b"audio data"
    file_obj = io.BytesIO(file_content)

    blob = gcs_module.put_tts_audio_file(signature, file_obj)
    expected_blob_path = f"{gcs_module.RADIO_SHOW_AUDIO_DIR}/{signature}.mp3"
    assert blob.name == expected_blob_path, "Blob のパスが正しく生成されている"
    assert blob._content == file_content, "アップロードした音声ファイルの内容が一致する"


def test_put_rss_xml_file(fake_bucket, monkeypatch):
    # last_build_date は UTC 時刻として与え、内部で JST へ変換される
    last_build_date = datetime(2025, 2, 9, 10, 0, 0, tzinfo=ZoneInfo("UTC"))
    # JST への変換後のフォーマットにより signature が生成される
    jst_date = last_build_date.astimezone(ZoneInfo("Asia/Tokyo"))
    signature = jst_date.strftime("%Y%m%d_%H%M%S_0900")
    prefix_dir = "latest_all"
    suffix_dir = "non"
    xml_content = "<rss></rss>"
    file_obj = io.BytesIO(xml_content.encode("utf-8"))

    blob = gcs_module.put_rss_xml_file(
        last_build_date, prefix_dir, file_obj, suffix_dir
    )
    expected_blob_path = (
        f"{gcs_module.RSS_RAW_DIR}/{prefix_dir}_{suffix_dir}/{signature}.xml"
    )
    assert blob.name == expected_blob_path, "RSS XML ファイルのパスが正しい"
    assert blob._content == xml_content.encode("utf-8"), (
        "XML の内容が正しくアップロードされている"
    )


def test_put_oai_pmh_json(fake_bucket, fixed_now, monkeypatch):
    monkeypatch.setattr(gcs_module, "get_now", lambda: fixed_now)
    signature = "test_signature"
    prefix_dir = "isbn"
    json_str = '{"data": "value"}'

    blob = gcs_module.put_oai_pmh_json(signature, prefix_dir, json_str)
    expected_blob_path = f"{gcs_module.OAI_PMH_RAW_DIR}/{prefix_dir}/{signature}.json"
    assert blob.name == expected_blob_path, "OAI-PMH JSON のパスが正しい"
    assert blob._content == json_str.encode("utf-8"), (
        "JSON の内容が正しくアップロードされている"
    )


def test_get_closest_cached_rss_file(fake_bucket):
    # 対象日時（UTC）を指定（関数内部で JST へ変換される）
    target_utc = datetime(2025, 2, 9, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
    prefix_dir = "latest_all"
    suffix_dir = "non"
    # RSS ファイルのパスのベースを生成
    prefix_base = f"{gcs_module.RSS_RAW_DIR}/{prefix_dir}_{suffix_dir}"
    search_prefix = (
        prefix_base
        + "/"
        + target_utc.astimezone(ZoneInfo("Asia/Tokyo")).strftime("%Y%m%d")
    )

    bucket = fake_bucket
    # 2 つの Blob を作成：古い方と新しい方
    older_blob_name = f"{search_prefix}/old.xml"
    newer_blob_name = f"{search_prefix}/new.xml"
    old_time = datetime(2025, 2, 9, 8, 0, 0, tzinfo=ZoneInfo("UTC"))
    new_time = datetime(2025, 2, 9, 9, 0, 0, tzinfo=ZoneInfo("UTC"))
    old_blob = bucket.blob(older_blob_name)
    old_blob.time_created = old_time
    old_blob._content = b"old rss content"
    new_blob = bucket.blob(newer_blob_name)
    new_blob.time_created = new_time
    new_blob._content = b"new rss content"

    result_io = gcs_module.get_closest_cached_rss_file(
        target_utc, prefix_dir, suffix_dir
    )
    result_content = result_io.read()
    # 新しい方 (new.xml) の内容が取得されるはず
    assert result_content == b"new rss content"


def test_get_closest_cached_oai_pmh_file(fake_bucket, monkeypatch):
    target_isbn = "9784621310328"
    prefix_dir = "isbn"
    prefix_base = f"{gcs_module.OAI_PMH_RAW_DIR}/{prefix_dir}"
    search_prefix = prefix_base + "/" + target_isbn

    bucket = fake_bucket
    # 2 つの Blob を作成：古いものと新しいもの
    old_blob_name = f"{search_prefix}/old.json"
    new_blob_name = f"{search_prefix}/new.json"
    old_time = datetime(2025, 2, 1, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
    new_time = datetime(2025, 2, 8, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
    old_blob = bucket.blob(old_blob_name)
    old_blob.time_created = old_time
    old_blob._content = b"old oai content"
    new_blob = bucket.blob(new_blob_name)
    new_blob.time_created = new_time
    new_blob._content = b"new oai content"

    # 固定の現在時刻を 2025-02-09 に設定（新しい Blob との差は 1 日）
    fixed_now = datetime(2025, 2, 9, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
    monkeypatch.setattr(gcs_module, "get_now", lambda: fixed_now)

    result_io = gcs_module.get_closest_cached_oai_pmh_file(target_isbn, prefix_dir)
    assert result_io is not None, "有効な OAI-PMH キャッシュが取得できる"
    result_content = result_io.read()
    assert result_content == b"new oai content"
