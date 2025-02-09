import io

import pytest

from src.blob import storage  # テスト対象のモジュール


class DummyBlob:
    def __init__(self, blob_path: str):
        self.blob_path = blob_path
        self.metadata = {}
        self.upload_called = False
        self.content_type = None
        self.predefined_acl = None
        self.file_content = None

    def upload_from_file(self, file, content_type: str, predefined_acl: str = None):
        self.upload_called = True
        self.content_type = content_type
        self.predefined_acl = predefined_acl
        file.seek(0)
        self.file_content = file.read()

    @property
    def public_url(self) -> str:
        return f"https://dummy.storage/{self.blob_path}"


class DummyBucket:
    def __init__(self):
        self.blobs = {}

    def blob(self, blob_path: str) -> DummyBlob:
        blob = DummyBlob(blob_path)
        self.blobs[blob_path] = blob
        return blob


@pytest.fixture
def dummy_bucket():
    return DummyBucket()


# すべてのテストで、get_bucket() をダミーの Bucket を返すように上書きする
@pytest.fixture(autouse=True)
def patch_get_bucket(monkeypatch, dummy_bucket):
    monkeypatch.setattr(storage, "_get_bucket", lambda: dummy_bucket)


# --- テストケース ---
def test_put_tts_audio_file(dummy_bucket):
    signature = "test_tts"
    file_obj = io.BytesIO(b"audio content")
    public_url = storage.put_tts_audio_file(signature, file_obj)
    expected_path = f"{storage.RADIO_SHOW_AUDIO_DIR}/{signature}.mp3"

    blob = dummy_bucket.blobs.get(expected_path)
    assert blob is not None, "Blob が作成されていない"
    assert blob.upload_called, "upload_from_file が呼ばれていない"
    assert blob.content_type == "audio/mpeg"
    assert blob.predefined_acl == "publicRead"
    assert public_url == f"https://dummy.storage/{expected_path}"
    assert blob.metadata.get("Cache-Control") == "public, max-age=604800"
    assert blob.metadata.get("content-type") == "audio/mpeg"
    assert "custom_time" in blob.metadata


def test_put_combined_json_file(dummy_bucket):
    signature = "test_json"
    file_obj = io.BytesIO(b'{"key": "value"}')
    public_url = storage.put_combined_json_file(signature, file_obj)
    expected_path = f"{storage.MASTERDATA_DIR}/{signature}.json"

    blob = dummy_bucket.blobs.get(expected_path)
    assert blob is not None, "Blob が作成されていない"
    assert blob.upload_called, "upload_from_file が呼ばれていない"
    # ACL 指定はしていない想定なので None であること
    assert blob.predefined_acl is None
    # JSON 用の content_type は "application/json" としてアップロードしている
    assert blob.content_type == "application/json"
    assert public_url == f"https://dummy.storage/{expected_path}"
    assert blob.metadata.get("Cache-Control") == "public, max-age=300"
    assert blob.metadata.get("content-type") == "application/json; charset=utf-8"
    assert "custom_time" in blob.metadata


def test_put_rss_xml_file(dummy_bucket):
    signature = "test_rss"
    file_obj = io.BytesIO(b"<rss></rss>")
    public_url = storage.put_rss_xml_file(signature, file_obj)
    expected_path = f"{storage.RSS_RAW_DIR}/{signature}.xml"

    blob = dummy_bucket.blobs.get(expected_path)
    assert blob is not None, "Blob が作成されていない"
    assert blob.upload_called, "upload_from_file が呼ばれていない"
    assert blob.content_type == "application/xml"
    assert public_url == f"https://dummy.storage/{expected_path}"
    assert blob.metadata.get("Cache-Control") == "public, max-age=300"
    assert blob.metadata.get("content-type") == "application/xml; charset=utf-8"
    assert "custom_time" in blob.metadata


def test_put_oai_pmh_json_file(dummy_bucket):
    signature = "test_oai"
    file_obj = io.BytesIO(b'{"data": "value"}')
    public_url = storage.put_oai_pmh_json_file(signature, file_obj)
    expected_path = f"{storage.OAI_PMH_RAW_DIR}/{signature}.json"

    blob = dummy_bucket.blobs.get(expected_path)
    assert blob is not None, "Blob が作成されていない"
    assert blob.upload_called, "upload_from_file が呼ばれていない"
    assert blob.content_type == "application/json"
    assert public_url == f"https://dummy.storage/{expected_path}"
    assert blob.metadata.get("Cache-Control") == "public, max-age=300"
    assert blob.metadata.get("content-type") == "application/json; charset=utf-8"
    assert "custom_time" in blob.metadata
