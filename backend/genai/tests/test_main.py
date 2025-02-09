import json
from datetime import datetime
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

import src.main as main_module
from src.book import book
from src.database.firestore import db
from src.event_sourcing import workflows
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
    def fake_exec_fetch_rss_and_oai_pmh_workflow(url, prefix, suffix, broadcasted_at):
        pass

    monkeypatch.setattr(
        main_module.workflows,
        "exec_fetch_rss_and_oai_pmh_workflow",
        fake_exec_fetch_rss_and_oai_pmh_workflow,
    )


@pytest.fixture(autouse=True)
def patch_workflows(monkeypatch):
    def fake_exec_run_agent_and_tts_workflow(
        radio_show_id, masterdata_blob_path, broadcasted_at
    ):
        pass

    monkeypatch.setattr(
        main_module.workflows,
        "exec_run_agent_and_tts_workflow",
        fake_exec_run_agent_and_tts_workflow,
    )


# tests for endpoints
client = TestClient(main_module.app)


def test_add_user(monkeypatch):
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


def test_add_radio_show(monkeypatch):
    # given
    dummy_id = str(uuid4())
    # ラジオ番組ドキュメントは空ではなく、何かしらのフィールドを入れて作成する
    radio_show_doc = db.collection("radio_shows").document(dummy_id)
    radio_show_doc.set({"status": "creating"})

    # when
    payload = {"id": "event1", "document": "radio_shows/" + dummy_id}
    response = client.post(
        "/add_radio_show",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )

    # then
    assert response.status_code == 204


def test_async_task_latest_all(monkeypatch):
    """
    KIND_LATEST_ALLのリクエストを送信し、204(No Content)が返ることを検証する
    """
    payload = {"kind": KIND_LATEST_ALL, "data": {"example_key": "example_value"}}
    response = client.post("/async_task", json=payload)
    assert response.status_code == 204


def test_async_task_latest_with_keywords_by_user(monkeypatch):
    """
    KIND_LATEST_WITH_KEYWORDS_BY_USERのリクエストを送信し、204(No Content)が返ることを検証する
    """
    payload = {
        "kind": KIND_LATEST_WITH_KEYWORDS_BY_USER,
        "data": {"user_id": 42, "keywords": ["fastapi", "pytest"]},
    }
    response = client.post("/async_task", json=payload)
    assert response.status_code == 204


def test_async_task_without_optional_data(monkeypatch):
    """
    オプション項目であるdataを省略した場合でも、バリデーションエラーが発生せず204が返ることを検証する
    """
    payload = {
        "kind": KIND_LATEST_ALL
        # dataは省略可能
    }
    response = client.post("/async_task", json=payload)
    assert response.status_code == 204


def test_async_task_invalid_payload(monkeypatch):
    """
    必須項目であるkindがない場合は、リクエストボディのバリデーションエラー(422)が発生することを検証する
    """
    payload = {"data": {"some": "data"}}
    response = client.post("/async_task", json=payload)
    assert response.status_code == 422  # Unprocessable Entity


@pytest.mark.parametrize(
    "broadcasted_at_str, expected_dt, desc",
    [
        # タイムゾーン指定なしの場合：そのまま UTC として解釈
        (
            "2025-02-09T12:34:56",
            datetime.fromisoformat("2025-02-09T12:34:56").replace(
                tzinfo=ZoneInfo("UTC")
            ),
            "naiveな日時はUTCとして解釈",
        ),
        # 明示的に UTC 指定の場合
        (
            "2025-02-09T12:34:56+00:00",
            datetime.fromisoformat("2025-02-09T12:34:56+00:00").astimezone(
                ZoneInfo("UTC")
            ),
            "UTC指定の日時",
        ),
        # JST指定の場合：正しくUTCに変換されるべき（12:34:56 JST -> 03:34:56 UTC）
        (
            "2025-02-09T12:34:56+09:00",
            datetime.fromisoformat("2025-02-09T12:34:56+09:00").astimezone(
                ZoneInfo("UTC")
            ),
            "JST指定の日時がUTCに変換される",
        ),
    ],
)
def test_async_task_broadcasted_at_timezones(
    monkeypatch, broadcasted_at_str, expected_dt, desc
):
    """
    broadcasted_at に対して、タイムゾーン指定の有無や JST指定の場合に正しくUTCに変換されるか検証するテスト
    """
    workflow_calls: list[Any] = []

    def dummy_exec_fetch_rss_and_oai_pmh_workflow(
        url, dir_base, test_param, broadcasted_at
    ):
        workflow_calls.append(broadcasted_at)

    # ワークフロー実行部分と URL 取得部分をモックする
    monkeypatch.setattr(
        workflows,
        "exec_fetch_rss_and_oai_pmh_workflow",
        dummy_exec_fetch_rss_and_oai_pmh_workflow,
    )
    monkeypatch.setattr(book, "latest_all", lambda: "http://dummy.url")

    request_body = {
        "kind": "latest_all",  # 実装側の定数と合わせる必要があります
        "data": {"broadcasted_at": broadcasted_at_str},
    }

    response = client.post("/async_task", json=request_body)
    assert response.status_code == 204, f"エンドポイント呼び出し失敗: {desc}"
    assert len(workflow_calls) == 1, f"ワークフローが呼ばれていません: {desc}"
    # 実際に渡された datetime が期待通り（UTC変換済み）であることを検証
    assert workflow_calls[0] == expected_dt, (
        f"{desc} のテストで、期待値と一致しません。"
    )
