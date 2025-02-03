import os
from contextlib import asynccontextmanager

import firebase_admin
import google.auth as gauth
import litellm
import vertexai
import weave
from cloudevents.http import from_http
from fastapi import FastAPI, Request, Response
from firebase_admin import auth
from firebase_admin import firestore_async as fb_async_firestore
from firebase_admin import storage as fb_storage
from google.cloud import firestore, storage
from lmnr import Laminar as L
from lmnr import observe
from smolagents import LiteLLMModel, ToolCallingAgent
from tenacity import retry, wait_exponential
from vertexai.generative_models import Content, GenerationConfig, Part
from vertexai.preview import rag
from vertexai.preview.generative_models import GenerativeModel, Tool

from src.logger import logger

if os.getenv("CI") == "true":
    # CI 環境では weave と Laminar を初期化しない
    pass
else:
    weave.init(project_name=os.getenv("WEAVE_PROJECT_NAME", ""))
    L.initialize(project_api_key=os.getenv("LMNR_PROJECT_API_KEY"))


# グローバル変数（Google Cloud SDK 用）
# Flask の app.config で環境変数を読み込んでいた部分は os.environ を利用
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
if not PROJECT_ID:
    raise Exception("Set GOOGLE_CLOUD_PROJECT environment variable.")

VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")
PUBLISHER_MODEL = "publishers/google/models/text-multilingual-embedding-002"
GENERATIVE_MODEL_NAME = "gemini-1.5-flash-001"
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

vertexai.init(project=PROJECT_ID, location=VERTEX_AI_LOCATION)
litellm._turn_on_debug()

if os.getenv("USE_FIREBASE_EMULATOR") == "true":
    emulator_project = PROJECT_ID
    bucket_name = f"{emulator_project}.appspot.com"
    firebase_admin.initialize_app(
        options={"projectId": emulator_project, "storageBucket": bucket_name}
    )

    # os.environ["GOOGLE_CLOUD_PROJECT"] = emulator_project  # override if needed
    db = firestore.Client(project=emulator_project)

    # storage_client = storage.Client(project=emulator_project)
    # storage_client = fb_storage

else:
    db = firestore.Client()
    storage_client = storage.Client()
    bucket_name = f"{PROJECT_ID}.firebasestorage.app"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting server...")

    # Firebase AuthのIdTokenのJWTを検証することが必要なのでFirebase Admin SDKを利用する
    options = {}
    if os.getenv("USE_FIREBASE_EMULATOR") == "true":
        logger.warning("Using Firebase Emulator")
        emulator_project = "local"
        options = {
            "projectId": emulator_project,
            "storageBucket": f"{emulator_project}.appspot.com",
        }

    firebase_admin.initialize_app(options=options)
    logger.info("Initialized Firebase Admin SDK")

    yield

    # リソースを解放する

    logger.info("Stopping server...")


# FastAPI アプリ作成
app = FastAPI(
    lifespan=lifespan,
)


# 複数ファイルの import は 1 ファイルずつしか実行できないため、指数バックオフ付きでリトライ
@retry(wait=wait_exponential(multiplier=5, max=40))
def import_files(corpus_name, gcs_path):
    return rag.import_files(
        corpus_name,
        [gcs_path],
        chunk_size=RAG_CHUNK_SIZE,
        chunk_overlap=RAG_CHUNK_OVERLAP,
        max_embedding_requests_per_min=RAG_MAX_EMBEDDING_REQUESTS_PER_MIN,
    )


# ============================
# エンドポイント実装
# ============================
@app.post("/add_user")
async def add_user(request: Request):
    body = await request.body()
    event = from_http(request.headers, body)
    document = event.get("document")
    event_id = event.get("id")

    # document は "users/uid" の形式であると想定
    users, uid = document.split("/")
    logger.info(f"{event_id}: start adding a user: {uid}")

    embedding_model_config = rag.EmbeddingModelConfig(publisher_model=PUBLISHER_MODEL)

    logger.info(f"{event_id}: start creating a rag corpus for a user: {uid}")
    rag_corpus = rag.create_corpus(
        display_name=uid,
        embedding_model_config=embedding_model_config,
    )
    logger.info(f"{event_id}: finished creating a rag corpus for a user: {uid}")

    doc_ref = db.collection(users).document(uid)
    doc_ref.update({"corpusName": rag_corpus.name, "status": "created"})

    logger.info(f"{event_id}: finished adding a user: {uid}")
    return Response(content="finished", status_code=204)


@app.post("/add_source")
async def add_source(request: Request):
    body = await request.body()
    event = from_http(request.headers, body)
    event_id = event.get("id")
    document = event.get("document")
    # document は "users/uid/notebooks/notebookId/sources/sourceId" の形式
    users, uid, notebooks, notebookId, sources, sourceId = document.split("/")

    logger.info(f"{event_id}: start adding a source: {sourceId}")

    user_ref = db.collection(users).document(uid)
    user = user_ref.get()
    corpus_name = user.get("corpusName")

    doc_ref = (
        db.collection(users)
        .document(uid)
        .collection(notebooks)
        .document(notebookId)
        .collection(sources)
        .document(sourceId)
    )
    doc = doc_ref.get()
    name = doc.get("name")
    storagePath = doc.get("storagePath")

    gcs_path = f"gs://{PROJECT_ID}.firebasestorage.app{storagePath}"

    logger.info(f"{event_id}: start importing a source file: {name}")
    response_import = import_files(corpus_name, gcs_path)
    logger.info(f"{event_id}: finished importing a source file: {response_import}")

    logger.info(f"{event_id}: start finding rag_file_id: {name}")
    rag_files = rag.list_files(corpus_name=corpus_name)
    rag_file_name = ""
    filename = storagePath.split("/")[-1]
    for rag_file in rag_files:
        if rag_file.display_name == filename:
            rag_file_name = rag_file.name
    rag_file_id = rag_file_name.split("/")[-1]
    logger.info(f"{event_id}: found rag_file_id: {rag_file_id}")

    doc_ref.update({"status": "created", "ragFileId": rag_file_id})
    logger.info(
        f"{event_id}: finished adding a source: {sourceId} / {name} => {rag_file_id}"
    )

    return Response(content="finished", status_code=204)


@app.post("/question")
async def question(request: Request):
    body = await request.body()
    event = from_http(request.headers, body)
    event_id = event.get("id")
    document = event.get("document")
    # document は "users/uid/notebooks/notebookId/chat/messageId" の形式
    users, uid, notebooks, notebookId, chat, messageId = document.split("/")

    logger.info(f"{event_id}: start generating an answer: {messageId}")

    message_ref = (
        db.collection(users)
        .document(uid)
        .collection(notebooks)
        .document(notebookId)
        .collection(chat)
        .document(messageId)
    )
    message = message_ref.get()

    # モデルからのメッセージの場合はスキップ
    if message.get("role") == "model":
        return Response(content="skip message from model", status_code=204)

    # 回答用の空ドキュメントを追加
    add_time, answer_ref = (
        db.collection(users)
        .document(uid)
        .collection(notebooks)
        .document(notebookId)
        .collection(chat)
        .add(
            {
                "content": "",
                "loading": True,
                "ragFileIds": None,
                "role": "model",
                "createdAt": firestore.SERVER_TIMESTAMP,
            }
        )
    )

    user_ref = db.collection(users).document(uid)
    user = user_ref.get()
    corpus_name = user.get("corpusName")

    source_ids = message.get("ragFileIds")
    logger.info(f"{event_id}: {len(source_ids)} sources are selected")

    rag_retrieval_tool = Tool.from_retrieval(
        retrieval=rag.Retrieval(
            source=rag.VertexRagStore(
                rag_resources=[
                    rag.RagResource(rag_corpus=corpus_name, rag_file_ids=source_ids)
                ],
                similarity_top_k=RAG_SIMILARITY_TOP_K,
                vector_distance_threshold=RAG_VECTOR_DISTANCE_THRESHOLD,
            ),
        )
    )

    rag_model = GenerativeModel(
        model_name=GENERATIVE_MODEL_NAME,
        tools=[rag_retrieval_tool],
        system_instruction=["Output the result in markdown format."],
    )

    chat_messages = (
        db.collection(users)
        .document(uid)
        .collection(notebooks)
        .document(notebookId)
        .collection("chat")
        .order_by("createdAt")
        .stream()
    )

    contents = [
        Content(
            role=chat_message.get("role"),
            parts=[Part.from_text(chat_message.get("content"))],
        )
        for chat_message in chat_messages
        if not chat_message.get("loading") and chat_message.get("status") == "success"
    ]
    logger.info(f"{event_id}: {len(contents)} contents are used")

    try:
        logger.info(f"{event_id}: start generating content")
        response_model = rag_model.generate_content(contents=contents)
        logger.info(f"{event_id}: finished generating content")

        answer_ref.update(
            {
                "content": response_model.text,
                "loading": False,
                "status": "success",
            }
        )
        message_ref.update({"loading": False, "status": "success"})
        logger.info(f"{event_id}: finished generating an answer: {messageId}")
    except Exception as err:
        message_ref.update({"loading": False, "status": "failed"})
        answer_ref.update(
            {
                "content": QUESTION_FAILED_MESSAGE,
                "loading": False,
                "status": "failed",
            }
        )
        logger.info(
            f"{event_id}: failed generating an answer: err={err}, type(err)={type(err)}"
        )

    return Response(content="finished", status_code=204)


@app.post("/summarize")
async def summarize(request: Request):
    body = await request.body()
    event = from_http(request.headers, body)
    event_id = event.get("id")
    document = event.get("document")
    # document は "users/uid/notebooks/notebookId/sources/sourceId" の形式
    users, uid, notebooks, notebookId, sources, sourceId = document.split("/")

    logger.info(f"{event_id}: start summarizing a source: {sourceId}")

    doc_ref = (
        db.collection(users)
        .document(uid)
        .collection(notebooks)
        .document(notebookId)
        .collection(sources)
        .document(sourceId)
    )
    doc = doc_ref.get()

    file_type = doc.get("type")
    storagePath = doc.get("storagePath")
    gcs_path = f"gs://{PROJECT_ID}.firebasestorage.app{storagePath}"

    model = GenerativeModel(model_name=GENERATIVE_MODEL_NAME)
    doc_part = Part.from_uri(gcs_path, file_type)

    config = GenerationConfig(
        max_output_tokens=MAX_SUMMARIZATION_LENGTH + 1000,
        temperature=0,
        top_p=1,
        top_k=32,
    )

    prompt = f"""You are an AI assistant.

Summarize the contents for readers who doesn't have enough domain knowledge.
Output the result in Japanese and the result must be less than {MAX_SUMMARIZATION_LENGTH} characters.
Surround the keypoint sentence or words by **.
"""

    try:
        logger.info(f"{event_id}: start generating a summary for a source: {sourceId}")
        response_model = model.generate_content(
            [doc_part, prompt], generation_config=config
        )
        logger.info(
            f"{event_id}: finished generating a summary for a source: {sourceId}"
        )
        doc_ref.update({"summarization": response_model.text})
        logger.info(f"{event_id}: finished summarizing a source: {sourceId}")
    except Exception as err:
        logger.info(f"{event_id}: failed generating a summary for a source: {sourceId}")
        doc_ref.update({"summarization": SUMMARIZATION_FAILED_MESSAGE})
        logger.info(
            f"{event_id}: failed summarizing a source: err={err}, type(err)={type(err)}"
        )

    return Response(content="finished", status_code=204)


@app.post("/hcheck")
async def hcheck():
    """ヘルスチェック用エンドポイント"""
    return Response(content="finished", status_code=200)


if __name__ == "__main__":
    # see: https://github.com/googleapis/google-auth-library-python/blob/main/google/auth/_default.py#L577-L595
    _, project_id = gauth.default()
    logger.info("project_id: %s", project_id)

    # db で何が入っているか確認するので、countとかを使ってみる
    users = db.collection("users").stream()
    print("users count: ", len(list(users)))

    # storageも何が入っているか確認する
    bucket = fb_storage.bucket()
    print("bucket: ", bucket.name)

    model_id = "vertex_ai/gemini-1.5-flash"
    model = LiteLLMModel(
        model_id,
        temperature=0.08,
    )

    agent = ToolCallingAgent(
        tools=[],
        model=model,
    )

    print(agent.run("Hello"))
