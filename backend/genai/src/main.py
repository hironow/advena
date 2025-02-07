import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

import firebase_admin
import google.auth as gauth
import litellm
import weave
from cloudevents.http import from_http
from fastapi import FastAPI, Request, Response
from firebase_admin import auth
from google.cloud import firestore, storage
from lmnr import Laminar as L
from lmnr import observe
from smolagents import LiteLLMModel, ToolCallingAgent
from tenacity import retry, wait_exponential
from vertexai.generative_models import Content, GenerationConfig, Part
from vertexai.preview import rag
from vertexai.preview.generative_models import GenerativeModel, Tool

from src.database.firestore import db
from src.logger import logger
from src.utils import get_now, is_valid_uuid

if os.getenv("CI") == "true":
    # CI 環境では weave と Laminar を初期化しない
    pass
else:
    weave.init(project_name=os.getenv("WEAVE_PROJECT_NAME", ""))
    L.initialize(project_api_key=os.getenv("LMNR_PROJECT_API_KEY"))


PUBLISHER_MODEL = "publishers/google/models/text-multilingual-embedding-002"
GENERATIVE_MODEL_NAME = "gemini-2.0-flash-001"  # see: https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models#gemini-models
RAG_CHUNK_SIZE = 512
RAG_CHUNK_OVERLAP = 100
RAG_MAX_EMBEDDING_REQUESTS_PER_MIN = 900
RAG_SIMILARITY_TOP_K = 3
RAG_VECTOR_DISTANCE_THRESHOLD = 0.5
QUESTION_FAILED_MESSAGE = (
    "申し訳ございません。回答の生成に失敗しました。再度質問をやり直してください。"
)
MAX_SUMMARIZATION_LENGTH = 2048
MAX_TOTAL_COMMON_QUESTIONS_LENGTH = 1024
SUMMARIZATION_FAILED_MESSAGE = "申し訳ございません。要約の生成に失敗しました。"
MEANINGFUL_MINIMUM_QUESTION_LENGTH = 7

gcp_project = None
firebase_app = None
# client
storage_client: storage.Client | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global gcp_project, firebase_app, db  # storage
    logger.info("Starting server...")

    gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT")
    # Firebase AuthのIdTokenのJWTを検証することが必要なのでFirebase Admin SDKを利用する
    options = {}
    if os.getenv("USE_FIREBASE_EMULATOR") == "true":
        logger.warning("Using Firebase Emulator")
        options = {
            "projectId": gcp_project,
            "storageBucket": f"{gcp_project}.appspot.com",
        }

    firebase_app = firebase_admin.initialize_app(options=options)
    logger.info("Initialized Firebase Admin SDK")

    storage_client = storage.Client()

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
    # # see: https://github.com/googleapis/google-auth-library-python/blob/main/google/auth/_default.py#L577-L595
    # _, project_id = gauth.default()
    # logger.info("project_id: %s", project_id)

    # # db で何が入っているか確認するので、countとかを使ってみる
    # users = db.collection("users").stream()
    # print("users count: ", len(list(users)))

    # # storageも何が入っているか確認する
    # bucket = fb_storage.bucket()
    # print("bucket: ", bucket.name)
    # blobs = bucket.list_blobs()
    # print("blobs count: ", len(list(blobs)))

    # # llm agent
    # model_id = "vertex_ai/gemini-1.5-flash"
    # model = LiteLLMModel(
    #     model_id,
    #     temperature=0.08,
    # )
    # agent = ToolCallingAgent(
    #     tools=[],
    #     model=model,
    # )
    # print(agent)
    # print(type(agent))
    # # print(agent.run("Hello"))
    pass
