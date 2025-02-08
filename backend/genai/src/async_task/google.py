import json
import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from google.cloud import tasks  # type: ignore
from google.protobuf import duration_pb2, timestamp_pb2
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.logger import logger

# 現状、queueは worker 1つのみを想定
WORKER_QUEUE_NAME = "worker"

cloudtasks_client = tasks.CloudTasksClient()


def _create_http_task(
    url: str,
    json_payload: dict[str, Any],
    scheduled_seconds_from_now: int | None = None,
    task_id: str | None = None,
    deadline_in_seconds: int | None = None,
) -> tasks.Task:
    """
    HTTP POST タスクを JSON ペイロードで作成する

    Args:
        url: タスクの送信先 URL
        json_payload: 送信する JSON ペイロード
        scheduled_seconds_from_now: 現在時刻からの遅延秒数
        task_id: タスクに付与する ID（指定があれば）
        deadline_in_seconds: タスクの処理期限（秒）

    Returns:
        作成された Cloud Tasks の Task オブジェクト
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "")

    task = tasks.Task(
        http_request=tasks.HttpRequest(
            http_method=tasks.HttpMethod.POST,
            url=url,
            headers={"Content-type": "application/json"},
            body=json.dumps(json_payload).encode("utf-8"),
        ),
        name=(
            cloudtasks_client.task_path(
                project_id, location, WORKER_QUEUE_NAME, task_id
            )
            if task_id is not None
            else None
        ),
    )

    # convert scheduled_seconds_from_now to protobuf Timestamp
    if scheduled_seconds_from_now is not None:
        # 遅延はまさに投入する直前からの秒数とする
        utcnow = datetime.now(UTC)
        schedule_time = utcnow + timedelta(seconds=scheduled_seconds_from_now)
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(schedule_time)
        task.schedule_time = timestamp
    # convert deadline_in_seconds to protobuf Duration
    if deadline_in_seconds is not None:
        duration = duration_pb2.Duration()
        duration.FromSeconds(deadline_in_seconds)
        task.dispatch_deadline = duration
    # send the task to Cloud Tasks
    return cloudtasks_client.create_task(
        tasks.CreateTaskRequest(
            parent=cloudtasks_client.queue_path(
                project_id, location, WORKER_QUEUE_NAME
            ),
            task=task,
        )
    )


@retry(
    wait=wait_exponential(multiplier=1, min=1, max=60),
    stop=stop_after_attempt(10),
    retry=retry_if_exception_type(Exception),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _enqueue_with_retry(
    url: str,
    json_payload: dict[str, Any],
    scheduled_seconds_from_now: int | None,
    task_id: str | None,
    deadline_in_seconds: int | None,
) -> tasks.Task:
    """retryとして、指数バックオフで最大10回リトライする"""
    return _create_http_task(
        url,
        json_payload,
        scheduled_seconds_from_now,
        task_id,
        deadline_in_seconds,
    )


def enqueue_async_task(
    kind: str,
    data: dict[str, Any] | None = None,
    scheduled_seconds_from_now: int | None = None,
    task_id: str | None = None,
    deadline_in_seconds: int | None = None,
) -> tasks.Task | None:
    """
    非同期タスク (/async_task) を Cloud Tasks にキュー追加する

    Args:
        kind: タスクの種類 (AsyncTaskBody の kind フィールド)
        data: タスクに付随するデータ (AsyncTaskBody の data フィールド)
        scheduled_seconds_from_now: 現在時刻からの遅延秒数
        task_id: タスクに付与する ID（任意）
        deadline_in_seconds: タスクの処理期限（秒）

    Returns:
        作成されたタスク（成功時）
    """
    # エンドポイントは /async_task 固定
    self_endpoint = os.getenv("GOOGLE_CLOUD_SELF_ENDPOINT_URL", "")
    url = f"{self_endpoint}/async_task"
    json_payload: dict[str, Any] = {"kind": kind, "data": data}

    try:
        task = _enqueue_with_retry(
            url,
            json_payload,
            scheduled_seconds_from_now,
            task_id,
            deadline_in_seconds,
        )
        logger.info("Task enqueued successfully. : %s", task)
        return task
    except Exception as e:
        logger.error("Max retries reached. Failing to enqueue task. : %s", e)
        raise
