import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import src.main as main_module
from src.database.firestore import db


# --- CloudEvent のパースのパッチ ---
@pytest.fixture(autouse=True)
def patch_from_http(monkeypatch):
    def fake_from_http(headers, body):
        # テストでは、リクエストボディの JSON をそのまま dict として扱う
        return json.loads(body)

    monkeypatch.setattr(main_module, "from_http", fake_from_http)


# --- Cloud Storage のパッチ ---
# @pytest.fixture(autouse=True)
# def patch_storage(monkeypatch):
#     class DummyBlob:
#         def delete(self):
#             return True

#     class DummyBucket:
#         def blob(self, name):
#             return DummyBlob()

#     class DummyStorageClient:
#         def bucket(self, bucket_name):
#             return DummyBucket()

#     monkeypatch.setattr(main_module.storage, "Client", lambda: DummyStorageClient())


# * tests for endpoints
client = TestClient(main_module.app)


def test_add_user():
    # given
    dummy_id = str(uuid4())
    # ユーザードキュメントは空ではなく、何かしらのフィールドを入れて作成する
    user_doc = db.collection("users").document(dummy_id)
    user_doc.set({"status": "creating"})

    # when
    payload = {"id": "event1", "document": "users/" + dummy_id}
    response = client.post(
        "/add_user",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )

    # then
    assert response.status_code == 204
