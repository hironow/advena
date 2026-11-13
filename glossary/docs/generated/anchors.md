<!-- 生成物。`just generate` が `Glossary/*.lean` から作る。手で編集しない。 -->

# 実装との対応

各用語が実装のどこに当たるか。対応が切れると `just check` が落ちる。

## Starter

実装との対応を持つ用語はない。

## advena 新刊ラジオ

| 用語 | ID | ファイル | そこにあるべき文字列 |
|---|---|---|---|
| 新着書誌フィード | `ndlFeed` | `backend/genai/src/book/book.py` | `def latest_all` |
| 新着書誌フィード | `ndlFeed` | `backend/genai/src/book/feed.py` | `httpx.get(url, timeout=300)` |
| フィード項目 | `feedItem` | `backend/genai/src/book/feed.py` | `class FeedEntry(BaseModel)` |
| フィード項目 | `feedItem` | `backend/genai/src/book/feed.py` | `def convert_to_entry_item` |
| 項目日時 | `itemDate` | `backend/genai/src/book/feed.py` | `published_parsed = feed.get("published_parsed")` |
| 項目日時 | `itemDate` | `backend/genai/src/event_sourcing/workflows.py` | `future[link] = mst_book` |
| 書誌メタデータ | `bibMetadata` | `backend/genai/src/book/oai_pmh.py` | `def get_metadata_by_isbn` |
| 書誌メタデータ | `bibMetadata` | `backend/genai/src/book/oai_pmh.py` | `def get_metadata_by_jp_e_code` |
| 結合マスタデータ | `masterdata` | `backend/genai/src/blob/storage.py` | `MASTERDATA_DIR = f"{PRIVATE_DIR}/masterdata"` |
| 結合マスタデータ | `masterdata` | `backend/genai/src/event_sourcing/workflows.py` | `rss_sig = last_build_date.strftime` |
| 収集実行 | `collectionRun` | `backend/genai/src/main.py` | `KIND_LATEST_ALL = "latest_all"` |
| 収集実行 | `collectionRun` | `backend/genai/src/event_sourcing/workflows.py` | `def exec_fetch_rss_and_oai_pmh_workflow` |
| 収集実行 | `collectionRun` | `backend/genai/src/event_sourcing/workflows.py` | `creating = entity_radio_show.new(result_blob.name, broadcasted_at)` |
| 番組対象日 | `broadcastDay` | `backend/genai/src/event_sourcing/workflows.py` | `exec_date_jst = datetime.now(JST)` |
| 番組対象日 | `broadcastDay` | `backend/genai/src/event_sourcing/workflows.py` | `elif published_date == target_date:` |
| 番組対象日 | `broadcastDay` | `backend/genai/src/event_sourcing/entity/radio_show.py` | `broadcasted_at: datetime | None = None` |
| 放送枠 | `broadcastSlot` | `docs/zenn-article.md` | `ラジオ番組の提供は1日1回のみです` |
| 番組文書 | `radioShow` | `backend/genai/src/event_sourcing/entity/radio_show.py` | `class RadioShow(RadioShowId)` |
| 番組文書 | `radioShow` | `backend/genai/src/event_sourcing/entity/radio_show.py` | `__collection__ = "radio_shows"` |
| 番組文書 | `radioShow` | `backend/genai/src/event_sourcing/entity/radio_show.py` | `radio_show_id = utils.new_id()` |
| 制作待ち | `showCreating` | `backend/genai/src/event_sourcing/entity/radio_show.py` | `status: Literal["creating"] | Literal["created"]` |
| 制作待ち | `showCreating` | `backend/genai/src/event_sourcing/entity/radio_show.py` | `status="creating"` |
| 文書作成イベント | `docCreatedEvent` | `scripts/bind-eventarc-invoke.sh` | `--event-filters="type=google.cloud.firestore.document.v1.created"` |
| 文書作成イベント | `docCreatedEvent` | `scripts/bind-eventarc-invoke.sh` | `--destination-run-path="/${ADD_RADIO_SHOW_PATH}"` |
| 文書作成イベント | `docCreatedEvent` | `scripts/update-eventarc-trigger.sh` | `--ack-deadline 300` |
| 再配信 | `redelivery` | `scripts/update-eventarc-trigger.sh` | `--min-retry-delay 300` |
| 再配信 | `redelivery` | `scripts/update-eventarc-trigger.sh` | `--max-retry-delay 600` |
| 配信打ち切り | `deadLetter` | `scripts/update-eventarc-trigger.sh` | `--dead-letter-topic $DEAD_LETTER_TOPIC` |
| 配信打ち切り | `deadLetter` | `scripts/update-eventarc-trigger.sh` | あってはならない: `--max-delivery-attempts` |
| 配信打ち切り | `deadLetter` | `scripts/bind-eventarc-invoke.sh` | `subscriptionは手動で作成する` |
| 番組台本 | `showScript` | `backend/genai/src/blob/storage.py` | `blob_path = f"{RADIO_SHOW_SCRIPT_DIR}/{signature}.txt"` |
| 番組台本 | `showScript` | `backend/genai/src/event_sourcing/workflows.py` | `script_blob = put_tts_script_file(radio_show_id, script)` |
| 番組台本 | `showScript` | `backend/genai/src/llm/agent.py` | `def extract_script_block` |
| 番組音声 | `showAudio` | `backend/genai/src/blob/storage.py` | `blob_path = f"{RADIO_SHOW_AUDIO_DIR}/{signature}.mp3"` |
| 番組音声 | `showAudio` | `backend/genai/src/event_sourcing/workflows.py` | `audio_blob = put_tts_audio_file(radio_show_id, bs)` |
| 番組音声 | `showAudio` | `backend/genai/src/tts/google.py` | `VOICE_NAME = "ja-JP-Neural2-B"` |
| 制作実行 | `productionRun` | `backend/genai/src/main.py` | `if doc.status == "created":` |
| 制作実行 | `productionRun` | `backend/genai/src/main.py` | `workflows.exec_run_agent_and_tts_workflow(` |
| 制作実行 | `productionRun` | `backend/genai/src/event_sourcing/workflows.py` | `def exec_run_agent_and_tts_workflow` |
| 制作実行 | `productionRun` | `backend/genai/Dockerfile.prd` | `"uvicorn", "src.main:app", "--host"` |
| 該当なし | `noItemsDay` | `backend/genai/src/event_sourcing/workflows.py` | `if len(current) == 0:` |
| 該当なし | `noItemsDay` | `docs/zenn-article.md` | `新規出版がない日は提供されません` |
| 公開済み番組 | `publishedShow` | `backend/genai/src/event_sourcing/entity/radio_show.py` | `"status": "created"` |
| 公開済み番組 | `publishedShow` | `frontend/web/lib/firestore/client-db.ts` | `where("status", "==", "created")` |
| 公開済み番組 | `publishedShow` | `frontend/web/firestore.rules` | `allow read: if isSignedIn();` |
| 制作の中断 | `productionHalt` | `backend/genai/src/main.py` | `logger.error(f"/add_radio_show endpoint error: {e}")` |
| 制作の中断 | `productionHalt` | `backend/genai/src/event_sourcing/workflows.py` | `raise ValueError("recorded が取得できませんでした。")` |
| 過去日指定の収集 | `staffRerun` | `backend/genai/src/event_sourcing/entity/radio_show.py` | `過去日の指定をしたいときは datetime で作成時に指定する` |
| 過去日指定の収集 | `staffRerun` | `backend/genai/src/main.py` | `class DataForLatestAll(BaseModel)` |
| 聴取者 | `listener` | `frontend/web/auth.ts` | `const isAllowedDomain` |
| 聴取者 | `listener` | `frontend/web/firestore.rules` | `function isSignedIn()` |
| 利用者文書 | `userDoc` | `frontend/web/lib/firestore/admin-db.ts` | `export const addUserAdmin` |
| 利用者文書 | `userDoc` | `backend/genai/src/main.py` | `async def add_user(request: Request):` |
| 利用者文書 | `userDoc` | `backend/genai/src/event_sourcing/entity/user.py` | `if doc.get("status") == "creating":` |
| 登録キーワード | `userKeyword` | `backend/genai/src/event_sourcing/entity/user_keyword.py` | `class Keyword(KeywordId)` |
| 登録キーワード | `userKeyword` | `frontend/web/firestore.rules` | `match /keywords/{keywordId}` |
| キーワード番組 | `keywordShow` | `backend/genai/src/main.py` | `KIND_LATEST_WITH_KEYWORDS_BY_USER = "latest_with_keywords_by_user"` |
| キーワード番組 | `keywordShow` | `docs/zenn-article.md` | `キーワードを登録すると、そのキーワードのためのラジオ番組が提供されます` |
| 状態の命名規約 | `statusConvention` | `frontend/web/lib/firestore/admin-db.ts` | `// -ingは「command」として、-edは「event」として使われ` |
| 状態の命名規約 | `statusConvention` | `frontend/web/lib/firestore/admin-db.ts` | `// deleting: documentの削除中` |
| 状態の命名規約 | `statusConvention` | `backend/genai/src/event_sourcing/entity/radio_show.py` | あってはならない: `Literal["deleting"]` |
| 状態の命名規約 | `statusConvention` | `backend/genai/src/event_sourcing/entity/radio_show.py` | あってはならない: `Literal["error"]` |
| 状態の命名規約 | `statusConvention` | `backend/genai/src/event_sourcing/entity/user.py` | あってはならない: `Literal["deleting"]` |
| 状態の命名規約 | `statusConvention` | `backend/genai/src/event_sourcing/entity/user.py` | あってはならない: `Literal["error"]` |

