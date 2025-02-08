import os
from contextlib import asynccontextmanager
from typing import Any

import firebase_admin
import google.auth as gauth
from cloudevents.http import from_http
from fastapi import FastAPI, Request, Response
from firebase_admin import auth
from tenacity import retry, wait_exponential

from src.database.firestore import db
from src.logger import logger
from src.utils import get_now, is_valid_uuid

firebase_app = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global firebase_app
    logger.info("Starting server...")

    gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT")
    # Firebase AuthのIdTokenのJWTを検証することが必要なのでFirebase Admin SDKを利用する
    options = {}
    if os.getenv("USE_FIREBASE_EMULATOR") == "true":
        logger.warning("Using Firebase Emulator")
        options: dict[str, Any] = {
            "projectId": gcp_project,
            "storageBucket": f"{gcp_project}.appspot.com",
        }

    firebase_app = firebase_admin.initialize_app(options=options)
    logger.info("Initialized Firebase Admin SDK")

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
    if db is None:
        logger.error("db is None")
        raise Exception("db is None")

    body = await request.body()
    event = from_http(request.headers, body)
    logger.info(f"event: {event}")
    document = event.get("document")
    event_id = event.get("id")

    now = get_now()

    logger.info(f"{event_id}: start adding a document: {document}")
    # TODO: 抽象化できていないので、修正が必要
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


@app.post("/hcheck")
async def hcheck():
    """ヘルスチェック用エンドポイント"""
    return Response(content="finished", status_code=200)


if __name__ == "__main__":
    # see: https://github.com/googleapis/google-auth-library-python/blob/main/google/auth/_default.py#L577-L595
    _, project_id = gauth.default()
    logger.info("project_id: %s", project_id)

    # # storageも何が入っているか確認する
    # bucket = fb_storage.bucket()
    # print("bucket: ", bucket.name)
    # blobs = bucket.list_blobs()
    # print("blobs count: ", len(list(blobs)))
