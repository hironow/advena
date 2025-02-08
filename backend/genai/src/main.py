import os
from contextlib import asynccontextmanager
from typing import Any

import google.auth as gauth
from cloudevents.http import from_http
from fastapi import FastAPI, Request, Response
from tenacity import retry, wait_exponential

from src.database.firestore import db
from src.logger import logger
from src.utils import get_now, is_valid_uuid


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting server...")
    # リソースを確保する
    logger.info("Started server...")
    yield
    # リソースを解放する
    logger.info("Stopping server...")


# FastAPI アプリ作成
app = FastAPI(
    lifespan=lifespan,
)


# ============================
# endpoints
# ============================
@app.post("/add_user")
async def add_user(request: Request):
    """[COMMAND] creating users"""
    # cloud event からのリクエストを受け取る
    body = await request.body()
    event = from_http(request.headers, body)  # type: ignore
    logger.info(f"event: {event}")
    document = event.get("document")
    event_id = event.get("id")

    now = get_now()

    logger.info(f"{event_id}: start adding a document: {document}")
    # FIXME: 抽象化できていないので、修正が必要
    # document は "users/{userId}" の形式であると想定
    if "/" not in document or document.count("/") != 1:
        logger.error(f"{event_id}: invalid document: {document}")
        return Response(content="invalid document", status_code=400)

    users, user_id = document.split("/")
    logger.info(f"{event_id}: start adding collection: {users} in a user: {user_id}")

    if not is_valid_uuid(user_id):
        logger.error(f"{event_id}: invalid user_id: {user_id}")
        return Response(content="invalid user_id", status_code=400)

    # firestoreから取得
    user = db.collection(users).document(user_id).get()
    if not user.exists:
        logger.error(f"{event_id}: user {user_id} is not found")
        return Response(content="user not found", status_code=404)

    if user.get("status") == "created":
        logger.error(f"{event_id}: user {user_id} is already created")
        return Response(content="user already created", status_code=204)

    db.collection(users).document(user_id).update(
        {
            "status": "created",
            "updated_at": now,
        }
    )

    logger.info(f"{event_id}: finished adding a user for {user_id} as created")
    return Response(content="finished", status_code=204)


# cloud scheduler からの非同期処理を一手に引き受けるエンドポイント
@app.post("/async_task")
async def async_task(request: Request):
    """[COMMAND] async task"""
    # cloud eventではないので、jsonとして処理
    body = await request.json()
    logger.info(f"async task body: {body}")

    # TODO: ここで非同期処理をmatchで振り分ける

    return Response(content="finished", status_code=204)


@app.post("/hcheck")
async def hcheck():
    """ヘルスチェック用エンドポイント"""
    return Response(content="finished", status_code=200)


if __name__ == "__main__":
    # see: https://github.com/googleapis/google-auth-library-python/blob/main/google/auth/_default.py#L577-L595
    _, project_id = gauth.default()
    logger.info("project_id: %s", project_id)
