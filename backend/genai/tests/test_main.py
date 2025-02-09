import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import src.main as main_module
from src.database.firestore import db
from src.main import KIND_LATEST_ALL, KIND_LATEST_WITH_KEYWORDS_BY_USER


# cloudevnts からのリクエストボディを dict に変換する関数をモックする
@pytest.fixture(autouse=True)
def patch_from_http(monkeypatch):
    def fake_from_http(headers, body):
        # テストでは、リクエストボディの JSON をそのまま dict として扱う
        return json.loads(body)

    monkeypatch.setattr(main_module, "from_http", fake_from_http)


# workflowsのmock
@pytest.fixture(autouse=True)
def patch_workflows(monkeypatch):
    def fake_exec_fetch_rss_and_oai_pmh_workflow(url, prefix, suffix):
        pass

    monkeypatch.setattr(
        main_module.workflows,
        "exec_fetch_rss_and_oai_pmh_workflow",
        fake_exec_fetch_rss_and_oai_pmh_workflow,
    )


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


def test_async_task_latest_all():
    """
    KIND_LATEST_ALLのリクエストを送信し、204(No Content)が返ることを検証する
    """
    payload = {"kind": KIND_LATEST_ALL, "data": {"example_key": "example_value"}}
    response = client.post("/async_task", json=payload)
    assert response.status_code == 204


def test_async_task_latest_with_keywords_by_user():
    """
    KIND_LATEST_WITH_KEYWORDS_BY_USERのリクエストを送信し、204(No Content)が返ることを検証する
    """
    payload = {
        "kind": KIND_LATEST_WITH_KEYWORDS_BY_USER,
        "data": {"user_id": 42, "keywords": ["fastapi", "pytest"]},
    }
    response = client.post("/async_task", json=payload)
    assert response.status_code == 204


def test_async_task_without_optional_data():
    """
    オプション項目であるdataを省略した場合でも、バリデーションエラーが発生せず204が返ることを検証する
    """
    payload = {
        "kind": KIND_LATEST_ALL
        # dataは省略可能
    }
    response = client.post("/async_task", json=payload)
    assert response.status_code == 204


def test_async_task_invalid_payload():
    """
    必須項目であるkindがない場合は、リクエストボディのバリデーションエラー(422)が発生することを検証する
    """
    payload = {"data": {"some": "data"}}
    response = client.post("/async_task", json=payload)
    assert response.status_code == 422  # Unprocessable Entity
