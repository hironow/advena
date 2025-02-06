import json

import pytest
from fastapi.testclient import TestClient
from mockfirestore import MockFirestore

import src.main as main_module


# --- CloudEvent のパースのパッチ ---
@pytest.fixture(autouse=True)
def patch_from_http(monkeypatch):
    def fake_from_http(headers, body):
        # テストでは、リクエストボディの JSON をそのまま dict として扱う
        return json.loads(body)

    monkeypatch.setattr(main_module, "from_http", fake_from_http)


@pytest.fixture(autouse=True)
def patch_firestore(monkeypatch):
    mock_db = MockFirestore()
    monkeypatch.setattr(main_module, "db", mock_db)


# --- firestore.Increment と SERVER_TIMESTAMP のパッチ ---
@pytest.fixture(autouse=True)
def patch_firestore_increment_and_server_timestamp(monkeypatch):
    monkeypatch.setattr(main_module.firestore, "Increment", lambda x: x)
    monkeypatch.setattr(main_module.firestore, "SERVER_TIMESTAMP", 0)


# --- rag 関連のパッチ ---
@pytest.fixture(autouse=True)
def patch_rag(monkeypatch):
    def fake_create_corpus(display_name, embedding_model_config):
        class DummyCorpus:
            def __init__(self, name):
                self.name = name

        return DummyCorpus(f"corpus_for_{display_name}")

    monkeypatch.setattr(main_module.rag, "create_corpus", fake_create_corpus)

    def fake_import_files(corpus_name, gcs_path, **kwargs):
        return {"status": "imported", "gcs_path": gcs_path}

    monkeypatch.setattr(main_module.rag, "import_files", fake_import_files)

    def fake_list_files(corpus_name):
        class DummyRagFile:
            def __init__(self, display_name, name):
                self.display_name = display_name
                self.name = name

        return [
            DummyRagFile(
                display_name="dummy.txt",
                name=f"{corpus_name}/ragFiles/dummy_rag_file_id",
            )
        ]

    monkeypatch.setattr(main_module.rag, "list_files", fake_list_files)

    def fake_delete_file(rag_file):
        return True

    monkeypatch.setattr(main_module.rag, "delete_file", fake_delete_file)


# --- GenerativeModel.generate_content のパッチ ---
@pytest.fixture(autouse=True)
def patch_generate_content(monkeypatch):
    class DummyResponse:
        def __init__(self, text):
            self.text = text

    def fake_generate_content(self, contents, generation_config=None):
        # /question 用: 各 Part の text を連結して返す
        if isinstance(contents, list) and contents and hasattr(contents[0], "parts"):
            combined = " ".join([part.text for c in contents for part in c.parts])
            return DummyResponse(f"Answer: {combined}")
        return DummyResponse("Dummy generated text")

    monkeypatch.setattr(
        main_module.GenerativeModel, "generate_content", fake_generate_content
    )


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
    db = main_module.db
    # ユーザードキュメントは空ではなく、何かしらのフィールドを入れて作成する
    user_doc = db.collection("users").document("testuser")
    user_doc.set({"dummy": True})

    # when
    payload = {"id": "event1", "document": "users/testuser"}
    response = client.post(
        "/add_user",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )

    # then
    assert response.status_code == 204


def test_add_source():
    # given
    db = main_module.db
    # ユーザー文書作成（既に存在する状態）
    user_doc = db.collection("users").document("testuser")
    user_doc.set({"corpusName": "corpus_for_testuser"})
    # ノートブック文書の作成
    notebook_doc = (
        db.collection("users")
        .document("testuser")
        .collection("notebooks")
        .document("testnb")
    )
    notebook_doc.set({"dummy": True})
    # ソース文書の作成
    source_doc = notebook_doc.collection("sources").document("testsource")
    source_doc.set({"name": "dummy.txt", "storagePath": "/dummy/path/dummy.txt"})

    # when
    payload = {
        "id": "event2",
        "document": "users/testuser/notebooks/testnb/sources/testsource",
    }
    response = client.post(
        "/add_source",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )

    # then
    assert response.status_code == 204


def test_question():
    # given
    db = main_module.db
    # ユーザードキュメント作成
    user_doc = db.collection("users").document("testuser")
    user_doc.set({"corpusName": "corpus_for_testuser"})
    # ノートブックとチャット文書の作成
    notebook_doc = user_doc.collection("notebooks").document("testnb")
    notebook_doc.set({"dummy": True})
    chat_doc = notebook_doc.collection("chat").document("msg1")
    chat_doc.set(
        {
            "role": "user",
            "content": "What is test?",
            "ragFileIds": ["dummy_rag_file_id"],
            "loading": False,
            "status": "success",
            "createdAt": 0,
        }
    )

    # when
    payload = {"id": "event3", "document": "users/testuser/notebooks/testnb/chat/msg1"}
    response = client.post(
        "/question",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )

    # then
    assert response.status_code == 204


def test_summarize():
    # given
    db = main_module.db
    # ユーザー、ノートブック、ソース文書の作成
    user_doc = db.collection("users").document("testuser")
    user_doc.set({"corpusName": "corpus_for_testuser"})
    notebook_doc = user_doc.collection("notebooks").document("testnb")
    notebook_doc.set({"dummy": True})
    source_doc = notebook_doc.collection("sources").document("testsource")
    source_doc.set({"type": "text/plain", "storagePath": "/dummy/path/dummy.txt"})

    # when
    payload = {
        "id": "event5",
        "document": "users/testuser/notebooks/testnb/sources/testsource",
    }
    response = client.post(
        "/summarize",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )

    # then
    assert response.status_code == 204
