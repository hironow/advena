from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import google.auth as gauth
from cloudevents.http import from_http  # type: ignore
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

from src import utils
from src.blob import storage
from src.book import book
from src.database.firestore import db
from src.event_sourcing import workflows
from src.event_sourcing.entity import radio_show as entity_radio_show
from src.logger import logger


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
    """[COMMAND] creating user"""
    try:
        # cloud event からのリクエストを受け取る
        body = await request.body()
        event = from_http(request.headers, body)  # type: ignore
        logger.info(f"event: {event}")
        document = event.get("document")
        event_id = event.get("id")

        now = utils.get_now()

        logger.info(f"{event_id}: start adding a document: {document}")
        # FIXME: 抽象化できていないので、修正が必要
        # document は "users/{userId}" の形式であると想定
        if "/" not in document or document.count("/") != 1:
            logger.error(f"{event_id}: invalid document: {document}")
            return Response(content="invalid document", status_code=400)

        users, user_id = document.split("/")
        logger.info(
            f"{event_id}: start adding collection: {users} in a user: {user_id}"
        )

        if not utils.is_valid_uuid(user_id):
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
    except Exception as e:
        logger.error(f"error: {e}")
        return Response(content="error", status_code=500)


@app.post("/add_radio_show")
async def add_radio_show(request: Request):
    """[COMMAND] creating radio_show"""
    try:
        # cloud event からのリクエストを受け取る
        body = await request.body()
        event = from_http(request.headers, body)  # type: ignore
        logger.info(f"event: {event}")
        document = event.get("document")
        event_id = event.get("id")

        now = utils.get_now()

        logger.info(f"{event_id}: start adding a document: {document}")
        # FIXME: 抽象化できていないので、修正が必要
        # document は "radio_shows/{radioShowId}" の形式であると想定
        if "/" not in document or document.count("/") != 1:
            logger.error(f"{event_id}: invalid document: {document}")
            return Response(content="invalid document", status_code=400)

        radio_shows, radio_show_id = document.split("/")
        logger.info(
            f"{event_id}: start adding collection: {radio_shows} in a radio_show: {radio_show_id}"
        )
        if (
            not utils.is_valid_uuid(radio_show_id)
            or radio_shows != entity_radio_show.RadioShow.__collection__
        ):
            logger.error(f"{event_id}: invalid radio_show_id: {radio_show_id}")
            return Response(content="invalid radio_show_id", status_code=400)

        # firestoreから取得
        doc = entity_radio_show.get(radio_show_id)
        if doc is None:
            logger.error(f"{event_id}: radio_show {radio_show_id} is not found")
            return Response(content="radio_show not found", status_code=404)

        if doc.status == "created":
            logger.error(f"{event_id}: radio_show {radio_show_id} is already created")
            return Response(content="radio_show already created", status_code=204)

        # start workflow
        masterdata_blob_path = doc.masterdata_blob_path
        broadcasted_at = doc.broadcasted_at
        workflows.exec_run_agent_and_tts_workflow(
            radio_show_id,
            masterdata_blob_path,
            broadcasted_at,
        )

        logger.info(
            f"{event_id}: finished adding a radio_show for {radio_show_id} as created"
        )
        return Response(content="finished", status_code=204)
    except Exception as e:
        logger.error(f"/add_radio_show endpoint error: {e}")
        return Response(content="error", status_code=500)


class AsyncTaskBody(BaseModel):
    kind: str
    data: dict[str, Any] | None = None  # kindに応じてkey-valueでデータを受け取る


KIND_LATEST_ALL = "latest_all"
KIND_LATEST_WITH_KEYWORDS_BY_USER = "latest_with_keywords_by_user"


# cloud scheduler からの非同期処理を一手に引き受けるエンドポイント
@app.post("/async_task")
async def async_task(body: AsyncTaskBody):
    """[COMMAND] async task"""
    logger.info(f"async task kind: {body.kind}, data: {body.data}")

    # TODO: cloud schedulerからの定期的な非同期処理(eventarc経由ではない)
    # NOTE: Fan-Outパターンで処理を分散するパターンも考えられる

    if body.kind == KIND_LATEST_ALL:
        # dataには `broadcasted_at` が含まれる場合がある
        broadcasted_at: datetime | None = None
        if body.data:
            broadcasted_at_str = body.data.get("broadcasted_at")
            if broadcasted_at_str:
                dt = datetime.fromisoformat(broadcasted_at_str)
                # tzinfoが既にある場合はUTCに変換、ない場合はUTCとして解釈
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=ZoneInfo("UTC"))
                else:
                    dt = dt.astimezone(ZoneInfo("UTC"))
                broadcasted_at = dt
                logger.info(f"broadcasted_at: {broadcasted_at}")

        # start latest_all workflow
        url = book.latest_all()
        workflows.exec_fetch_rss_and_oai_pmh_workflow(
            url, storage.XML_LATEST_ALL_DIR_BASE, "test", broadcasted_at
        )
    elif body.kind == KIND_LATEST_WITH_KEYWORDS_BY_USER:
        # start latest_with_keywords_by_user for each user workflow
        pass

    return Response(status_code=204)


@app.post("/hcheck")
async def hcheck():
    """ヘルスチェック用エンドポイント"""
    return Response(content="finished", status_code=200)


if __name__ == "__main__":
    # see: https://github.com/googleapis/google-auth-library-python/blob/main/google/auth/_default.py#L577-L595
    _, project_id = gauth.default()
    logger.info("project_id: %s", project_id)
