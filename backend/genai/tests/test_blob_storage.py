import io
from datetime import datetime, timezone

import pytest

import src.blob.storage as gcs_module

# もし gcs_module 内で UTC が定義されていればそれを、なければ timezone.utc を利用
UTC = getattr(gcs_module, "UTC", timezone.utc)


class FakeBlob:
    def __init__(self, name, time_created=None, download_content=b""):
        self.name = name
        self.time_created = time_created
        self.download_content = download_content
        self.metadata = None
        self.public_url = f"https://fake.storage/{name}"

    def upload_from_file(self, file_obj, content_type, predefined_acl=None):
        self.upload_from_file_called = True
        # ファイル先頭にシークしてから全読み込み
        file_obj.seek(0)
        self.upload_content = file_obj.read()
        self.content_type = content_type
        self.predefined_acl = predefined_acl

    def upload_from_string(self, s, content_type, predefined_acl=None):
        self.upload_from_string_called = True
        self.upload_string = s
        self.content_type = content_type
        self.predefined_acl = predefined_acl

    def download_to_file(self, file_obj):
        file_obj.write(self.download_content)


class FakeBucket:
    def __init__(self, blobs=None):
        self._blobs = blobs or []
        self.name = "fake_bucket"

    def blob(self, blob_path):
        # テストでは各呼び出し毎に同一の FakeBlob を返す必要がある場合、後で monkeypatch で上書きすることも可能
        return FakeBlob(blob_path)

    def list_blobs(self, prefix, max_results):
        # _blobs に登録された Blob のうち、prefix で始まるものを返す
        return [blob for blob in self._blobs if blob.name.startswith(prefix)]


def test_get_bucket(monkeypatch):
    # _get_bucket は、gcs_module.storage_client.bucket(...) を利用しているので、
    # storage_client の bucket メソッドを FakeClient で上書きする
    fake_bucket = FakeBucket()
    FakeClient = type(
        "FakeClient",
        (),
        {"bucket": lambda self, bucket_name, user_project: fake_bucket},
    )
    monkeypatch.setattr(gcs_module, "storage_client", FakeClient())
    bucket = gcs_module._get_bucket()
    assert bucket == fake_bucket


def test_upload_blob_file(monkeypatch):
    blob_path = "test/path/file.txt"
    file_content = b"file data"
    file_obj = io.BytesIO(file_content)
    metadata = {"foo": "bar"}
    content_type = "text/plain"
    acl = "publicRead"

    # FakeBucket を生成し、blob() の返り値を固定する
    fake_bucket = FakeBucket()
    fake_blob = FakeBlob(blob_path)
    # ここでは FakeBucket.blob() を常に fake_blob を返すように上書き
    monkeypatch.setattr(fake_bucket, "blob", lambda path: fake_blob)
    monkeypatch.setattr(gcs_module, "_get_bucket", lambda: fake_bucket)

    public_url = gcs_module._upload_blob_file(
        blob_path, file_obj, metadata, content_type, acl
    )
    # _upload_blob_file 内で、blob.metadata に metadata が設定される
    assert fake_blob.metadata == metadata
    assert hasattr(fake_blob, "upload_from_file_called")
    assert fake_blob.upload_content == file_content
    assert fake_blob.content_type == content_type
    assert fake_blob.predefined_acl == acl
    assert public_url == fake_blob.public_url


def test_upload_blob_string(monkeypatch):
    blob_path = "test/path/file.txt"
    s = "test content"
    metadata = {"foo": "bar"}
    content_type = "text/plain"
    acl = "private"

    fake_bucket = FakeBucket()
    fake_blob = FakeBlob(blob_path)
    monkeypatch.setattr(fake_bucket, "blob", lambda path: fake_blob)
    monkeypatch.setattr(gcs_module, "_get_bucket", lambda: fake_bucket)

    public_url = gcs_module._upload_blob_string(
        blob_path, s, metadata, content_type, acl
    )
    assert fake_blob.metadata == metadata
    assert hasattr(fake_blob, "upload_from_string_called")
    assert fake_blob.upload_string == s
    assert fake_blob.content_type == content_type
    assert fake_blob.predefined_acl == acl
    assert public_url == fake_blob.public_url


def test_put_tts_audio_file_success(monkeypatch):
    signature = "testsig"
    file_content = b"audio data"
    file_obj = io.BytesIO(file_content)

    fake_bucket = FakeBucket()
    blob_path_expected = f"{gcs_module.RADIO_SHOW_AUDIO_DIR}/{signature}.mp3"
    fake_blob = FakeBlob(blob_path_expected)
    monkeypatch.setattr(fake_bucket, "blob", lambda path: fake_blob)
    monkeypatch.setattr(gcs_module, "_get_bucket", lambda: fake_bucket)

    public_url = gcs_module.put_tts_audio_file(signature, file_obj)
    assert hasattr(fake_blob, "upload_from_file_called")
    # アップロード時の content_type と predefined_acl が指定されていること
    assert fake_blob.content_type == "audio/mpeg"
    assert fake_blob.predefined_acl == "publicRead"
    assert public_url == fake_blob.public_url


def test_put_tts_audio_file_empty_signature():
    with pytest.raises(ValueError):
        gcs_module.put_tts_audio_file("", io.BytesIO(b"data"))


def test_put_rss_xml_file_success(monkeypatch):
    signature = "rsssig"
    prefix_dir = "latest_all"
    suffix_dir = "non"
    file_content = b"<xml>content</xml>"
    file_obj = io.BytesIO(file_content)
    fake_bucket = FakeBucket()
    blob_path_expected = (
        f"{gcs_module.RSS_RAW_DIR}/{prefix_dir}_{suffix_dir}/{signature}.xml"
    )
    fake_blob = FakeBlob(blob_path_expected)
    monkeypatch.setattr(fake_bucket, "blob", lambda path: fake_blob)
    monkeypatch.setattr(gcs_module, "_get_bucket", lambda: fake_bucket)

    public_url = gcs_module.put_rss_xml_file(
        signature, prefix_dir, file_obj, suffix_dir
    )
    assert hasattr(fake_blob, "upload_from_file_called")
    # XML 用の content_type は "application/xml; charset=utf-8" となる
    # （実装内では "application/xml" でアップロードしているので注意）
    assert fake_blob.content_type == "application/xml"
    assert public_url == fake_blob.public_url


def test_put_rss_xml_file_empty_params():
    with pytest.raises(ValueError):
        gcs_module.put_rss_xml_file("", "some_prefix", io.BytesIO(b""))
    with pytest.raises(ValueError):
        gcs_module.put_rss_xml_file("sig", "", io.BytesIO(b""))


def test_put_oai_pmh_json_success(monkeypatch):
    signature = "oai_sig"
    prefix_dir = "isbn"
    json_str = '{"key": "value"}'
    fake_bucket = FakeBucket()
    blob_path_expected = f"{gcs_module.OAI_PMH_RAW_DIR}/{prefix_dir}/{signature}.json"
    fake_blob = FakeBlob(blob_path_expected)
    monkeypatch.setattr(fake_bucket, "blob", lambda path: fake_blob)
    monkeypatch.setattr(gcs_module, "_get_bucket", lambda: fake_bucket)

    public_url = gcs_module.put_oai_pmh_json(signature, prefix_dir, json_str)
    assert hasattr(fake_blob, "upload_from_string_called")
    assert fake_blob.upload_string == json_str
    # JSON 用の content_type は "application/json; charset=utf-8" となる
    # （実装内では "application/json" でアップロードしているので注意）
    assert fake_blob.content_type == "application/json"
    assert public_url == fake_blob.public_url


def test_put_oai_pmh_json_empty_params():
    with pytest.raises(ValueError):
        gcs_module.put_oai_pmh_json("", "prefix", "{}")
    with pytest.raises(ValueError):
        gcs_module.put_oai_pmh_json("sig", "", "{}")
    with pytest.raises(ValueError):
        gcs_module.put_oai_pmh_json("sig", "prefix", "")


def test_put_combined_json_file_success(monkeypatch):
    signature = "combined_sig"
    json_str = '{"combined": true}'
    fake_bucket = FakeBucket()
    blob_path_expected = f"{gcs_module.MASTERDATA_DIR}/{signature}.json"
    fake_blob = FakeBlob(blob_path_expected)
    monkeypatch.setattr(fake_bucket, "blob", lambda path: fake_blob)
    monkeypatch.setattr(gcs_module, "_get_bucket", lambda: fake_bucket)

    public_url = gcs_module.put_combined_json_file(signature, json_str)
    assert hasattr(fake_blob, "upload_from_string_called")
    assert fake_blob.upload_string == json_str
    assert fake_blob.content_type == "application/json"
    assert public_url == fake_blob.public_url


def test_put_combined_json_file_empty_params():
    with pytest.raises(ValueError):
        gcs_module.put_combined_json_file("", "{}")
    with pytest.raises(ValueError):
        gcs_module.put_combined_json_file("sig", "")


def test_get_closest_cached_rss_file_no_blobs(monkeypatch):
    target_utc = datetime(2025, 2, 9, 10, 20, 30, tzinfo=UTC)
    prefix_dir = "latest_all"
    suffix_dir = "non"
    fake_bucket = FakeBucket(blobs=[])
    monkeypatch.setattr(gcs_module, "_get_bucket", lambda: fake_bucket)

    result = gcs_module.get_closest_cached_rss_file(target_utc, prefix_dir, suffix_dir)
    assert result is None


def test_get_closest_cached_rss_file_success(monkeypatch):
    target_utc = datetime(2025, 2, 9, 0, 0, 0, tzinfo=UTC)
    prefix_dir = "latest_all"
    suffix_dir = "non"
    date_str = target_utc.strftime("%Y%m%d")
    # 2 つの Blob を用意。より新しい方（ time_created が大きい方）を返すはず
    blob_name1 = (
        f"{gcs_module.RSS_RAW_DIR}/{prefix_dir}_{suffix_dir}/{date_str}/file1.xml"
    )
    blob_name2 = (
        f"{gcs_module.RSS_RAW_DIR}/{prefix_dir}_{suffix_dir}/{date_str}/file2.xml"
    )
    time_created1 = datetime(2025, 2, 9, 1, 0, 0, tzinfo=UTC)
    time_created2 = datetime(2025, 2, 9, 2, 0, 0, tzinfo=UTC)
    fake_blob1 = FakeBlob(blob_name1, time_created1, download_content=b"content1")
    fake_blob2 = FakeBlob(blob_name2, time_created2, download_content=b"content2")
    fake_bucket = FakeBucket(blobs=[fake_blob1, fake_blob2])
    monkeypatch.setattr(gcs_module, "_get_bucket", lambda: fake_bucket)

    result = gcs_module.get_closest_cached_rss_file(target_utc, prefix_dir, suffix_dir)
    assert result is not None
    content = result.read()
    # より新しい blob の内容が取得されるはず
    assert content == b"content2"


def test_get_closest_cached_rss_file_invalid_params():
    with pytest.raises(ValueError):
        gcs_module.get_closest_cached_rss_file(datetime.now(UTC), "", "non")
    with pytest.raises(ValueError):
        gcs_module.get_closest_cached_rss_file(None, "latest_all", "non")


def test_get_closest_cached_oai_pmh_file_no_blobs(monkeypatch):
    target_isbn = "9781234567890"
    prefix_dir = "isbn"
    fake_bucket = FakeBucket(blobs=[])
    monkeypatch.setattr(gcs_module, "_get_bucket", lambda: fake_bucket)
    result = gcs_module.get_closest_cached_oai_pmh_file(target_isbn, prefix_dir)
    assert result is None


def test_get_closest_cached_oai_pmh_file_too_old(monkeypatch):
    target_isbn = "9781234567890"
    prefix_dir = "isbn"
    # 固定の現在時刻をセット
    fixed_now = datetime(2025, 2, 9, 10, 20, 30, tzinfo=UTC)
    monkeypatch.setattr(gcs_module, "get_now", lambda: fixed_now)
    # get_diff_days() には (now - past).days を返す簡易実装をセット
    monkeypatch.setattr(
        gcs_module, "get_diff_days", lambda now, past: (now - past).days
    )
    # 8日前の Blob を用意（7日以上前なので無効）
    old_time = datetime(2025, 2, 1, 10, 20, 30, tzinfo=UTC)
    fake_blob = FakeBlob("blob_old", old_time, download_content=b"old content")
    fake_bucket = FakeBucket(blobs=[fake_blob])
    monkeypatch.setattr(gcs_module, "_get_bucket", lambda: fake_bucket)
    result = gcs_module.get_closest_cached_oai_pmh_file(target_isbn, prefix_dir)
    assert result is None


def test_get_closest_cached_oai_pmh_file_success(monkeypatch):
    target_isbn = "9781234567890"
    prefix_dir = "isbn"
    fixed_now = datetime(2025, 2, 9, 10, 20, 30, tzinfo=UTC)
    monkeypatch.setattr(gcs_module, "get_now", lambda: fixed_now)
    monkeypatch.setattr(
        gcs_module, "get_diff_days", lambda now, past: (now - past).days
    )

    # 検索される prefix は以下のようになる:
    # "private/oai_pmh/isbn/9781234567890"
    blob_name_prefix = f"private/oai_pmh/{prefix_dir}/{target_isbn}"

    # 2つの Blob を用意。名前がプレフィックスにマッチするようにする
    time_created1 = datetime(2025, 2, 8, 10, 20, 30, tzinfo=UTC)
    time_created2 = datetime(2025, 2, 9, 9, 0, 0, tzinfo=UTC)
    fake_blob1 = FakeBlob(
        f"{blob_name_prefix}/file1.json", time_created1, download_content=b"old content"
    )
    fake_blob2 = FakeBlob(
        f"{blob_name_prefix}/file2.json", time_created2, download_content=b"new content"
    )

    fake_bucket = FakeBucket(blobs=[fake_blob1, fake_blob2])
    monkeypatch.setattr(gcs_module, "_get_bucket", lambda: fake_bucket)

    result = gcs_module.get_closest_cached_oai_pmh_file(target_isbn, prefix_dir)
    assert result is not None
    content = result.read()
    # より新しい方の Blob の内容が取得されるはず
    assert content == b"new content"


def test_get_closest_cached_oai_pmh_file_invalid_params():
    with pytest.raises(ValueError):
        gcs_module.get_closest_cached_oai_pmh_file("", "isbn")
    with pytest.raises(ValueError):
        gcs_module.get_closest_cached_oai_pmh_file("9781234567890", "")
