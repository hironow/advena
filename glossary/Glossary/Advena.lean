import Glossary.Claim

/-!
# advena 新刊ラジオの用語集

国立国会図書館の新着書誌フィードから、LLM が台本を、Cloud Text-to-Speech が音声を作り、
新刊紹介のラジオ番組を毎日公開するサービスの用語と主張。

開始点 B: 用語はコード（backend/genai, frontend/web, scripts）から起こした。
各用語の anchors は、その用語を実現している場所を指す。コードが変わると `just glossary check` が落ちる。
主張は「現行コードでは」と「提案では」を区別して書く。提案は Quint のモデルの中だけにあり、コードは変えていない。
-/

namespace Glossary.Advena

inductive Term where
  | ndlFeed | feedItem | itemDate | bibMetadata | coverImage | masterdata | collectionRun
  | broadcastDay | broadcastSlot | radioShow | showCreating
  | docCreatedEvent | redelivery | deadLetter
  | showScript | showAudio | productionRun | noItemsDay | publishedShow | productionHalt
  | staffRerun | listener | userDoc | userKeyword | keywordShow | statusConvention
  deriving DecidableEq, Repr

inductive Ctx where
  | collection | production | delivery | publication | account | operations
  deriving DecidableEq, Repr

open Term

def terms : List (Entry Term Ctx) := [
  { id := ndlFeed, label := "新着書誌フィード", context := .collection,
    gloss := "国立国会図書館サーチが提供する新着書誌の RSS。latest_all(size) が URL を組み立て、fetch_rss が 300 秒のタイムアウトで取得する。取得した XML は GCS の private/rss/ にキャッシュする",
    anchors := ["backend/genai/src/book/book.py#def latest_all",
                "backend/genai/src/book/feed.py#httpx.get(url, timeout=300)"] },
  { id := feedItem, label := "フィード項目", context := .collection,
    gloss := "新着書誌フィードの 1 項目。タイトル、要約、リンク、ISBN または JP-e コード、項目日時を持つ",
    defDeps := [ndlFeed],
    anchors := ["backend/genai/src/book/feed.py#class FeedEntry(BaseModel)",
                "backend/genai/src/book/feed.py#def convert_to_entry_item"] },
  { id := itemDate, label := "項目日時", context := .collection,
    gloss := "フィード項目の pubDate（feedparser の published）。split_books が JST の日付に直して番組対象日と比べ、過去・当日・未来に分ける。発売日ではない。NDL サーチの OpenSearch API で同じ記録を見ると、pubDate は時刻つきで発売日より前の日時（例: pubDate 2026-11-01 18:34、発売日 2026-12-11）で、発売日は dcterms:issued にある（2026-11-14 取得の 2 件で確認。advena が使う bib.xml の RSS で同じかは未確認）。NDL は pubDate の意味を文書で定義していない",
    defDeps := [feedItem],
    anchors := ["backend/genai/src/book/feed.py#published_parsed = feed.get(\"published_parsed\")",
                "backend/genai/src/event_sourcing/workflows.py#future[link] = mst_book"] },
  { id := bibMetadata, label := "書誌メタデータ", context := .collection,
    gloss := "ISBN または JP-e コードで OAI-PMH から取る書誌情報。private/oai_pmh/ にキャッシュする",
    defDeps := [feedItem],
    anchors := ["backend/genai/src/book/oai_pmh.py#def get_metadata_by_isbn",
                "backend/genai/src/book/oai_pmh.py#def get_metadata_by_jp_e_code"] },
  { id := coverImage, label := "書影", context := .collection,
    gloss := "本の表紙の画像。収集実行が ISBN または JP-e コードから NDL サーチの書影 API の URL を組み立て、番組の本の thumbnail_url として保存し、本棚に表示する。NDL はこの書影 API を 2026-03-31 に終了した（NDL サーチのお知らせ）ので、今は表示されない見込み（画面では確かめていない）",
    defDeps := [feedItem],
    anchors := ["backend/genai/src/book/book.py#THUMBNAIL_URL_BASE = \"https://ndlsearch.ndl.go.jp/thumbnail/\"",
                "frontend/web/components/shelf/Bookshelf.tsx#src={book.thumbnail_url}"] },
  { id := masterdata, label := "結合マスタデータ", context := .collection,
    gloss := "1 回の収集で得たフィード項目と書誌メタデータを結合した JSON。ファイル名は RSS の lastBuildDate から作り、private/masterdata/ に置く。番組文書はこのパスを持ち、制作実行はここから項目を選ぶ",
    defDeps := [feedItem, bibMetadata],
    anchors := ["backend/genai/src/blob/storage.py#MASTERDATA_DIR = f\"{PRIVATE_DIR}/masterdata\"",
                "backend/genai/src/event_sourcing/workflows.py#rss_sig = last_build_date.strftime"] },
  { id := collectionRun, label := "収集実行", context := .collection,
    gloss := "POST /async_task（kind=latest_all）で始まる処理。フィードと書誌を取り込み、結合マスタデータを書き、最後に制作待ちの番組文書を 1 つ作る。呼ばれるたびに新しい文書を作り、同じ日の文書が既にあるかは確かめない。起動元は Cloud Scheduler とされるが、ジョブの設定はリポジトリにない",
    defDeps := [ndlFeed, masterdata], assoc := [radioShow, staffRerun],
    anchors := ["backend/genai/src/main.py#KIND_LATEST_ALL = \"latest_all\"",
                "backend/genai/src/event_sourcing/workflows.py#def exec_fetch_rss_and_oai_pmh_workflow",
                "backend/genai/src/event_sourcing/workflows.py#creating = entity_radio_show.new(result_blob.name, broadcasted_at)"] },
  { id := broadcastDay, label := "番組対象日", context := .production,
    gloss := "その番組で紹介する本を選ぶ JST の日付。番組文書に broadcasted_at があればその日、無ければ制作実行を始めた時刻の JST 日付になる（exec_date_jst）。項目日時がこの日付に等しい項目だけを紹介する。公開時に broadcasted_at として書き戻され、一覧の並び順に使われる",
    defDeps := [itemDate], assoc := [productionRun, radioShow],
    anchors := ["backend/genai/src/event_sourcing/workflows.py#exec_date_jst = datetime.now(JST)",
                "backend/genai/src/event_sourcing/workflows.py#elif published_date == target_date:",
                "backend/genai/src/event_sourcing/entity/radio_show.py#broadcasted_at: datetime | None = None"] },
  { id := broadcastSlot, label := "放送枠", role := some .resource, context := .publication,
    gloss := "番組対象日 1 日につき 1 本だけ番組を公開できる、という枠。業務上の言明（docs/zenn-article.md「ラジオ番組の提供は1日1回のみです」）による。コードにはこの枠を守る確認がない",
    defDeps := [broadcastDay],
    anchors := ["docs/zenn-article.md#ラジオ番組の提供は1日1回のみです"] },
  { id := radioShow, label := "番組文書", context := .production,
    gloss := "Firestore の radio_shows コレクションの 1 文書。収集実行が status=creating で作り、制作実行が公開する。ID は新しい UUID で、番組対象日からは決まらない",
    defDeps := [masterdata],
    anchors := ["backend/genai/src/event_sourcing/entity/radio_show.py#class RadioShow(RadioShowId)",
                "backend/genai/src/event_sourcing/entity/radio_show.py#__collection__ = \"radio_shows\"",
                "backend/genai/src/event_sourcing/entity/radio_show.py#radio_show_id = utils.new_id()"] },
  { id := showCreating, label := "制作待ち", context := .production,
    gloss := "番組文書の status が creating の状態。配信を待っている、制作中、該当なしで配信が終わった後、配信が打ち切られた後、の 4 つの状況を区別しない。一覧には出ない",
    defDeps := [radioShow],
    anchors := ["backend/genai/src/event_sourcing/entity/radio_show.py#status: Literal[\"creating\"] | Literal[\"created\"]",
                "backend/genai/src/event_sourcing/entity/radio_show.py#status=\"creating\""] },
  { id := docCreatedEvent, label := "文書作成イベント", role := some .externalConfirmation, context := .delivery,
    gloss := "Firestore の文書作成を Eventarc が Pub/Sub の push で /add_radio_show に届けるもの。少なくとも 1 回届き、重複も遅延もある。アプリは届くのを止められない。購読の ack 期限は 300 秒（scripts の設定値。本番の実設定は確かめていない）",
    defDeps := [radioShow],
    anchors := ["scripts/bind-eventarc-invoke.sh#--event-filters=\"type=google.cloud.firestore.document.v1.created\"",
                "scripts/bind-eventarc-invoke.sh#--destination-run-path=\"/${ADD_RADIO_SHOW_PATH}\"",
                "scripts/update-eventarc-trigger.sh#--ack-deadline 300"] },
  { id := redelivery, label := "再配信", context := .delivery,
    gloss := "応答が成功でないか、ack 期限（300 秒）までに返らないとき、Pub/Sub が同じイベントをもう一度届けること。間隔は 300〜600 秒（scripts の設定値）。前の制作実行がまだ動いていても再配信は起きる",
    defDeps := [docCreatedEvent],
    anchors := ["scripts/update-eventarc-trigger.sh#--min-retry-delay 300",
                "scripts/update-eventarc-trigger.sh#--max-retry-delay 600"] },
  { id := deadLetter, label := "配信打ち切り", context := .delivery,
    gloss := "再配信が上限回数に達したイベントを dead letter トピックに移すこと。上限回数は scripts で指定しておらず Pub/Sub の既定値に従う。dead letter の購読は手動で作るとされ、番組文書の状態を変える処理はない",
    defDeps := [redelivery],
    anchors := ["scripts/update-eventarc-trigger.sh#--dead-letter-topic $DEAD_LETTER_TOPIC",
                "!scripts/update-eventarc-trigger.sh#--max-delivery-attempts",
                "scripts/bind-eventarc-invoke.sh#subscriptionは手動で作成する"] },
  { id := showScript, label := "番組台本", context := .production,
    gloss := "LLM の応答の <script> ブロックにある読み上げ文。public/radio_show_script/{番組文書の ID}.txt に保存し、公開 URL で配る。同じ番組の制作実行は同じパスに上書きする",
    defDeps := [radioShow],
    anchors := ["backend/genai/src/blob/storage.py#blob_path = f\"{RADIO_SHOW_SCRIPT_DIR}/{signature}.txt\"",
                "backend/genai/src/event_sourcing/workflows.py#script_blob = put_tts_script_file(radio_show_id, script)",
                "backend/genai/src/llm/agent.py#def extract_script_block"] },
  { id := showAudio, label := "番組音声", context := .production,
    gloss := "番組台本を Cloud Text-to-Speech（ja-JP-Neural2-B、MP3）で読み上げた音声。public/radio_show_audio/{番組文書の ID}.mp3 に上書き保存する",
    defDeps := [showScript],
    anchors := ["backend/genai/src/blob/storage.py#blob_path = f\"{RADIO_SHOW_AUDIO_DIR}/{signature}.mp3\"",
                "backend/genai/src/event_sourcing/workflows.py#audio_blob = put_tts_audio_file(radio_show_id, bs)",
                "backend/genai/src/tts/google.py#VOICE_NAME = \"ja-JP-Neural2-B\""] },
  { id := productionRun, label := "制作実行", context := .production,
    gloss := "文書作成イベント 1 回分の処理。/add_radio_show が status を読み、created なら 204 で終える。そうでなければ番組対象日の項目を選び、LLM で台本を作って保存し、音声を作って保存し、公開する。status の確認と公開は別々の書き込みで、その間を守る排他はない。uvicorn の 1 プロセスが、イベントループを止めたまま同期に実行する",
    defDeps := [docCreatedEvent, radioShow, broadcastDay, showScript, showAudio],
    anchors := ["backend/genai/src/main.py#if doc.status == \"created\":",
                "backend/genai/src/main.py#workflows.exec_run_agent_and_tts_workflow(",
                "backend/genai/src/event_sourcing/workflows.py#def exec_run_agent_and_tts_workflow",
                "backend/genai/Dockerfile.prd#\"uvicorn\", \"src.main:app\", \"--host\""] },
  { id := noItemsDay, label := "該当なし", context := .production,
    gloss := "番組対象日に項目日時が一致する項目が 0 件のこと。制作実行はログを残して戻り、/add_radio_show は 204 を返すので配信は成功で終わり、番組文書は制作待ちのまま残る。業務上の言明は「新規出版がない日は提供されません」",
    defDeps := [broadcastDay, productionRun, showCreating],
    anchors := ["backend/genai/src/event_sourcing/workflows.py#if len(current) == 0:",
                "docs/zenn-article.md#新規出版がない日は提供されません"] },
  { id := publishedShow, label := "公開済み番組", role := some .entitlement, context := .publication,
    gloss := "status が created の番組文書。番組音声と番組台本の公開 URL、紹介した本、番組対象日を持ち、サインインした全聴取者に一覧で見える。取り下げる手段はコードにない",
    defDeps := [radioShow, showScript, showAudio, broadcastDay],
    anchors := ["backend/genai/src/event_sourcing/entity/radio_show.py#\"status\": \"created\"",
                "frontend/web/lib/firestore/client-db.ts#where(\"status\", \"==\", \"created\")",
                "frontend/web/firestore.rules#allow read: if isSignedIn();"] },
  { id := productionHalt, label := "制作の中断", role := some .stop, context := .operations,
    gloss := "制作実行が途中で止まること。依存先（Gemini、Cloud Text-to-Speech、GCS）の失敗で例外になって 500 を返す場合と、Cloud Run のリクエストやインスタンスが打ち切られる場合がある。どちらも再配信に回る。止まっている間も、再配信の回数と時刻（番組対象日を制作時刻で決める場合はその日付）は進む",
    defDeps := [productionRun, redelivery],
    anchors := ["backend/genai/src/main.py#logger.error(f\"/add_radio_show endpoint error: {e}\")",
                "backend/genai/src/event_sourcing/workflows.py#raise ValueError(\"recorded が取得できませんでした。\")"] },
  { id := staffRerun, label := "過去日指定の収集", context := .operations,
    gloss := "運用者が /async_task に broadcasted_at を付けて呼び、過去の日の番組文書を作ること。radio_show.py のコメントが想定している。その日の番組が既にあっても作れる",
    defDeps := [collectionRun, broadcastDay],
    anchors := ["backend/genai/src/event_sourcing/entity/radio_show.py#過去日の指定をしたいときは datetime で作成時に指定する",
                "backend/genai/src/main.py#class DataForLatestAll(BaseModel)"] },
  { id := listener, label := "聴取者", context := .account,
    gloss := "許可されたドメインかメールアドレスの Google アカウントでサインインした人。公開済み番組の一覧を読める",
    anchors := ["frontend/web/auth.ts#const isAllowedDomain",
                "frontend/web/firestore.rules#function isSignedIn()"] },
  { id := userDoc, label := "利用者文書", context := .account,
    gloss := "users コレクションの 1 文書。サインイン時に firebase_uid で探し、無ければトランザクションの中で status=creating、version 0 で作る。/add_user が created にする。Python 側で読み出すときの移行（版 0 から 1）も creating を created に変える",
    defDeps := [listener],
    anchors := ["frontend/web/lib/firestore/admin-db.ts#export const addUserAdmin",
                "backend/genai/src/main.py#async def add_user(request: Request):",
                "backend/genai/src/event_sourcing/entity/user.py#if doc.get(\"status\") == \"creating\":"] },
  { id := userKeyword, label := "登録キーワード", context := .account,
    gloss := "users/{id}/keywords の文書。データの型はあるが、書き込む経路はコードにない（Firestore rules も write: false）",
    defDeps := [userDoc],
    anchors := ["backend/genai/src/event_sourcing/entity/user_keyword.py#class Keyword(KeywordId)",
                "frontend/web/firestore.rules#match /keywords/{keywordId}"] },
  { id := keywordShow, label := "キーワード番組", context := .publication,
    gloss := "登録キーワードで絞った番組。業務上は予定だが未実装で、/async_task の kind=latest_with_keywords_by_user は何もしない",
    defDeps := [userKeyword, publishedShow],
    anchors := ["backend/genai/src/main.py#KIND_LATEST_WITH_KEYWORDS_BY_USER = \"latest_with_keywords_by_user\"",
                "docs/zenn-article.md#キーワードを登録すると、そのキーワードのためのラジオ番組が提供されます"] },
  { id := statusConvention, label := "状態の命名規約", context := .production,
    gloss := "フロントのコメントにある規約。-ing は command、-ed は event として Eventarc で backend に通知する。creating、created、deleting、error を挙げるが、型にあるのは creating と created だけで、deleting と error を代入する箇所もない",
    defDeps := [radioShow, userDoc],
    anchors := ["frontend/web/lib/firestore/admin-db.ts#// -ingは「command」として、-edは「event」として使われ",
                "frontend/web/lib/firestore/admin-db.ts#// deleting: documentの削除中",
                "!backend/genai/src/event_sourcing/entity/radio_show.py#Literal[\"deleting\"]",
                "!backend/genai/src/event_sourcing/entity/radio_show.py#Literal[\"error\"]",
                "!backend/genai/src/event_sourcing/entity/user.py#Literal[\"deleting\"]",
                "!backend/genai/src/event_sourcing/entity/user.py#Literal[\"error\"]"] }
]

theorem terms_wellFormed : WellFormed terms := check_sound _ (by decide)

/-! ## 状態 creating の多義性（パターン 2）

コードの番組文書の状態は 2 つしかない（radio_show.py の `Literal["creating"] | Literal["created"]` の写し）。
番組文書が実際に置かれうる状況は、コードを読むと 5 つに分かれる。そのうち 4 つが同じ creating になる。 -/

/-- radio_show.py の status の写し。 -/
inductive DocStatus where
  | creating | created
  deriving DecidableEq, Repr

/-- 番組文書が置かれうる状況（コードを読んで分けたもの）。 -/
inductive Situation where
  /-- 文書は作られ、文書作成イベントの配信を待っている -/
  | awaitingDelivery
  /-- 制作実行が台本と音声を作っている -/
  | inProduction
  /-- 該当なしで 204 を返し、配信は成功として終わった -/
  | noItemsAcked
  /-- 再配信が上限に達し、配信が打ち切られた -/
  | deadLettered
  /-- 公開した -/
  | published
  deriving DecidableEq, Repr

/-- 各状況で文書が持つ status（radio_show.new は creating で作り、publish だけが created にする）。 -/
def statusOf : Situation → DocStatus
  | .published => .created
  | .awaitingDelivery | .inProduction | .noItemsAcked | .deadLettered => .creating

/-- その番組がまだ公開に向けて進む見込みがあるか。配信待ちと制作中だけが進む。 -/
def stillProgressing : Situation → Bool
  | .awaitingDelivery | .inProduction => true
  | .noItemsAcked | .deadLettered | .published => false

/-- status だけで「まだ進む」を判定できる関数がある、という命題。 -/
def StatusTellsProgress : Prop :=
  ∃ f : DocStatus → Bool, ∀ s : Situation, f (statusOf s) = stillProgressing s

/-- 配信待ちと該当なしは同じ creating なのに、進む見込みが逆なので、そのような関数はない。 -/
theorem creating_is_overloaded : ¬ StatusTellsProgress := by
  rintro ⟨f, hf⟩
  have hWaiting := hf .awaitingDelivery
  have hAbandoned := hf .noItemsAcked
  simp only [statusOf, stillProgressing] at hWaiting hAbandoned
  rw [hWaiting] at hAbandoned
  exact absurd hAbandoned (by decide)

/-! ## 番組対象日の決まり方

workflows.py の exec_run_agent_and_tts_workflow は、番組文書の broadcasted_at が無ければ、
制作実行を始めた時刻の JST 日付を番組対象日にする。日付は 1 始まりの通し番号で表す。 -/

/-- 番組対象日の決め方の写し。`stored` は番組文書の broadcasted_at、`productionDay` は制作実行を始めた日。 -/
def targetDay (stored : Option Nat) (productionDay : Nat) : Nat := stored.getD productionDay

/-- 番組対象日が番組文書だけで決まる（いつ制作しても同じ日になる）、という命題。 -/
def DayFixedByDocument : Prop :=
  ∀ (stored : Option Nat) (d₁ d₂ : Nat), targetDay stored d₁ = targetDay stored d₂

/-- broadcasted_at の無い文書を 1 日目と 2 日目に制作すると、番組対象日が変わる。 -/
theorem day_depends_on_production_time : ¬ DayFixedByDocument := by
  intro h
  exact absurd (h none 1 2) (by decide)

/-! ## モデルへの参照

Spec/radio_show.qnt のモジュール:
- code1: 現行コード、番組 1 つ、実行枠 2 つ（2 つの実行が同じ番組を並行に扱える）
- code2: 現行コード、番組 2 つ、実行枠 1 つ
- proposal1, proposal2: 提案の 4 点（作成時に日付を固定、世代つきの制作権、skipped、回収処理）を入れたもの。規模は code1, code2 と同じ
- noSweep1: 提案から回収処理だけを除いたもの
どれも JST の日付 2 日、再配信は 2 回まで。

Spec/account.qnt: 同じ firebase_uid での 2 つのサインイン。 -/

def radio (main invariant : String) : QuintRef :=
  { file := "Spec/radio_show.qnt", main, invariant }

def radioLiveness (main : String) : QuintRef :=
  { file := "Spec/radio_show.qnt", main, invariant := "Liveness", temporal := true }

def account (main invariant : String) : QuintRef :=
  { file := "Spec/account.qnt", main, invariant }

def claims : List (Claim Term) := [
  { about := [feedItem, masterdata, radioShow, publishedShow, productionRun],
    statement := "用語集は、ID が一意で、参照先が存在し、定義が循環していない",
    verdict := .proved,
    evidence := .lean "Glossary.Advena.terms_wellFormed" (WellFormed terms) terms_wellFormed },
  { about := [showCreating, noItemsDay, deadLetter, productionRun],
    statement := "現行コードでは、番組文書の status だけで、その番組がまだ公開に向けて進むのか、もう誰も扱わないのかを判別できる（status の写しと、コードから分けた 5 つの状況についての主張）",
    verdict := .counterexample,
    evidence := .leanRefutes "Glossary.Advena.creating_is_overloaded" StatusTellsProgress creating_is_overloaded },
  { about := [broadcastDay, radioShow, productionRun],
    statement := "現行コードでは、番組対象日は番組文書だけで決まり、いつ制作しても同じ日になる（番組対象日の決め方の写しについての主張）",
    verdict := .counterexample,
    evidence := .leanRefutes "Glossary.Advena.day_depends_on_production_time" DayFixedByDocument day_depends_on_production_time },
  -- 現行コード
  { about := [broadcastSlot, publishedShow, collectionRun, staffRerun],
    statement := "現行コードでは、1 つの番組対象日に公開済み番組は高々 1 本（番組 2 つ、実行枠 1 つ、2 日、再配信 2 回まで）",
    verdict := .counterexample, evidence := .violated (radio "code2" "onePerDay") },
  { about := [publishedShow, showScript, showAudio, redelivery, productionRun],
    statement := "現行コードでは、公開済み番組の台本と音声は同じ制作実行が書いたもの（ack 期限を過ぎた後の再配信を別のインスタンスが並行に処理する場合を含む。番組 1 つ、実行枠 2 つ）",
    verdict := .counterexample, evidence := .violated (radio "code1" "sameRun") },
  { about := [publishedShow, showScript, showAudio, redelivery],
    statement := "現行コードでは、公開した後に、公開 URL の先の台本と音声は変わらない（番組 1 つ、実行枠 2 つ）",
    verdict := .counterexample, evidence := .violated (radio "code1" "unchangedAfterPublish") },
  { about := [productionRun, redelivery, docCreatedEvent],
    statement := "現行コードでは、同じ番組を同時に制作する（LLM と TTS を呼びうる）実行は高々 1 つ（番組 1 つ、実行枠 2 つ）",
    verdict := .counterexample, evidence := .violated (radio "code1" "oneProducerAtATime") },
  { about := [productionHalt, broadcastDay, redelivery, publishedShow],
    statement := "現行コードでは、制作が中断して再配信が JST の 0 時をまたいでも、公開済み番組は本来の日（broadcasted_at、無ければ収集した日）の番組である",
    verdict := .counterexample, evidence := .violated (radio "code1" "dayAsIntended") },
  { about := [productionHalt, deadLetter, noItemsDay, showCreating],
    statement := "現行コードでは、番組を進める操作が公平に実行されるなら、制作の中断が何度起きても、作成された番組はいずれ公開などの終わりの状態に至る",
    verdict := .counterexample, evidence := .violated (radioLiveness "code1") },
  -- 提案（モデルの中だけ。コードは変えていない）
  { about := [broadcastSlot, broadcastDay, collectionRun, productionHalt],
    statement := "提案（番組対象日を作成時に固定して保存し、その日から文書の ID を作る、ほか 3 点）では、中断や 0 時またぎがあっても、1 つの番組対象日に公開済み番組は高々 1 本（番組 2 つ、実行枠 1 つ）",
    verdict := .proved, evidence := .holds (radio "proposal2" "onePerDay") },
  { about := [publishedShow, showScript, showAudio, redelivery, productionHalt],
    statement := "提案（status の確認をトランザクションにして制作権を世代つきで取り、台本と音声を世代ごとのパスに書き、世代が一致するときだけ公開する、ほか 3 点）では、公開済み番組の台本と音声は同じ制作実行が書いたもの（番組 1 つ、実行枠 2 つ）",
    verdict := .proved, evidence := .holds (radio "proposal1" "sameRun") },
  { about := [publishedShow, showScript, showAudio],
    statement := "提案では、公開した後に、公開 URL の先の台本と音声は変わらない（番組 1 つ、実行枠 2 つ）",
    verdict := .proved, evidence := .holds (radio "proposal1" "unchangedAfterPublish") },
  { about := [productionHalt, broadcastDay, publishedShow],
    statement := "提案では、制作が中断して再配信が JST の 0 時をまたいでも、公開済み番組は本来の日の番組である（番組 1 つ、実行枠 2 つ）",
    verdict := .proved, evidence := .holds (radio "proposal1" "dayAsIntended") },
  { about := [productionHalt, deadLetter, noItemsDay, showCreating],
    statement := "提案では、番組を進める操作（配信、制作の各段階、リースの期限切れ、回収処理）が公平に実行されるなら、制作の中断が何度起きても、作成された番組はいずれ公開・skipped・failed のどれかになる（番組 1 つ、実行枠 2 つ）",
    verdict := .proved, evidence := .holds (radioLiveness "proposal1") },
  { about := [productionHalt, deadLetter, showCreating],
    statement := "提案から回収処理だけを除いても、作成された番組はいずれ終わりの状態に至る",
    verdict := .counterexample, evidence := .violated (radioLiveness "noSweep1") },
  { about := [broadcastSlot, broadcastDay, collectionRun],
    statement := "提案から「作成時に番組対象日を固定して保存し、その日から文書の ID を作る」だけを除いても、1 つの番組対象日に公開済み番組は高々 1 本（番組 2 つ、実行枠 1 つ）",
    verdict := .counterexample, evidence := .violated (radio "noFixDay2" "onePerDay") },
  { about := [broadcastDay, productionHalt, publishedShow],
    statement := "提案から日付の固定だけを除いても、0 時をまたいだ再配信の後の公開済み番組は本来の日の番組である（番組 1 つ、実行枠 2 つ）",
    verdict := .counterexample, evidence := .violated (radio "noFixDay1" "dayAsIntended") },
  { about := [publishedShow, showScript, showAudio, redelivery],
    statement := "提案から世代つきの制作権だけを除いても、公開済み番組の台本と音声は同じ制作実行が書いたもの（番組 1 つ、実行枠 2 つ）",
    verdict := .counterexample, evidence := .violated (radio "noFence1" "sameRun") },
  { about := [noItemsDay, showCreating],
    statement := "提案から skipped だけを除いても、該当なしと確かめられた番組は failed にならない（回収処理が creating のままの番組を failed にする）",
    verdict := .counterexample, evidence := .violated (radio "noTerminal1" "noItemsNotFailed") },
  { about := [productionRun, redelivery],
    statement := "提案では、同じ番組を同時に制作する実行は高々 1 つ（リースが切れた後も古い実行は動き続けうる）",
    verdict := .counterexample, evidence := .violated (radio "proposal1" "oneProducerAtATime") },
  { about := [noItemsDay, showCreating],
    statement := "提案では、該当なしと確かめられた番組は failed にならない（skipped になる。failed は公開できなかった番組だけに使う）（番組 1 つ、実行枠 2 つ）",
    verdict := .proved, evidence := .holds (radio "proposal1" "noItemsNotFailed") },
  -- 利用者文書
  { about := [userDoc, listener],
    statement := "現行コードで、トランザクション内の検索が「該当なし」という結果を守らない場合でも、1 つの firebase_uid に利用者文書は高々 1 つ（同じ人の 2 つのサインイン）",
    verdict := .counterexample, evidence := .violated (account "accountUnguarded" "oneUserPerUid") },
  { about := [userDoc, listener],
    statement := "現行コードで、トランザクション内の検索が「該当なし」という結果も守る場合、1 つの firebase_uid に利用者文書は高々 1 つ（同じ人の 2 つのサインイン）",
    verdict := .proved, evidence := .holds (account "accountGuarded" "oneUserPerUid") },
  -- 業務への質問（業界の分類の出典は docs/business-gaps.md）
  { about := [feedItem, itemDate, broadcastDay],
    statement := "番組で紹介する「その日の本」は、その日に発売される本か、その日に NDL の記録が登録・更新された本か。現行コードは pubDate で選んでおり、後者に近い",
    verdict := .undecided,
    evidence := .questionOutsideModel "フィードのデータの意味の問題で、状態の遷移では示せない。根拠は NDL サーチの OpenSearch API の記録（pubDate と dcterms:issued が違う日）",
    industry := some (.answered "NDL のデータでは発売日は dcterms:issued にあり、pubDate は発売日より前の時刻つき日時だった（2 件を確認）。pubDate の定義を NDL は文書にしていない") },
  { about := [broadcastSlot, staffRerun, collectionRun],
    statement := "同じ番組対象日に番組が既にあるとき、運用者の再実行やスケジューラの再試行は、番組を差し替えるのか、2 本目として加えるのか、断るのか",
    verdict := .undecided, evidence := .question [radio "code2" "onePerDay"],
    industry := some (.answered "Podcast では差し替えが定まっている。エピソードの GUID は変えず、重複は処理されないか削除されうる（Apple）。Cloud Scheduler は同じ予定の重複実行がありうるとし、冪等な受け手を求める") },
  { about := [productionHalt, deadLetter, broadcastSlot],
    statement := "制作が失敗した日（配信打ち切り）の番組をどうするか。諦めるのか、遅れて作るのか、誰がいつ気づき、聴取者に何を見せるのか",
    verdict := .undecided, evidence := .question [radioLiveness "code1", radioLiveness "noSweep1"],
    industry := some (.gap "日次の自動生成音声で、生成に失敗した日の扱いを公表した例は見つからない。Spotify Daily Drive の更新漏れの苦情はある（コミュニティ投稿、二次情報）") },
  { about := [broadcastDay, productionHalt, collectionRun],
    statement := "broadcasted_at の無い番組の日付は、収集した日か、制作した日か。遅れて制作したとき、どちらの日の本を紹介するのか",
    verdict := .undecided, evidence := .question [radio "code1" "dayAsIntended"],
    industry := some (.answered "日次番組の題名の日付は放送枠の日付で、pubDate は公開時刻（NHK ラジオニュースの RSS で確認）。制作が遅れても枠の日付が番組の日付になる") },
  { about := [noItemsDay, showCreating, publishedShow],
    statement := "該当なしの日に、聴取者に何を見せるか。何も出さないのか、新刊がなかったと知らせるのか",
    verdict := .undecided, evidence := .question [radioLiveness "code1"],
    industry := some (.gap "空の日の指針は見つからない。日次ニュース番組は別の回で枠を埋め、Alexa は 7 日より古い項目を無視して「新しい内容がない」と告げる。聴取者への影響の証拠は弱い") },
  { about := [productionRun, redelivery, docCreatedEvent],
    statement := "1 本の番組のために LLM と TTS を何回まで呼んでよいか（費用）。重複を減らそうとリースを長くすると、止まった実行の後の再開が遅れる",
    verdict := .undecided, evidence := .question [radio "code1" "oneProducerAtATime", radio "proposal1" "oneProducerAtATime"],
    industry := some (.answered "Eventarc は少なくとも 1 回の配信で重複がありうるとし、event ID を鍵にした冪等なハンドラを勧める。Cloud Run もタイムアウト後に処理が続きうるとして冪等なリクエストを勧める") },
  { about := [userDoc, listener],
    statement := "同じ人が 2 つの端末からほぼ同時に初めてサインインしたとき、利用者文書が 2 つできることはあるか（Firestore のトランザクションが「該当なし」という検索結果を守るか）",
    verdict := .undecided, evidence := .question [account "accountUnguarded" "oneUserPerUid"],
    industry := some (.answered "Firestore は直列化可能な分離を保証すると明記する。ただし文書が説明するロックは読んだ文書単位で、検索結果が空の場合の仕組みは書かれていない") },
  { about := [publishedShow, statusConvention],
    statement := "公開済み番組を訂正または取り下げる手段を持つべきか。持つなら、誰が決め、聴取者に何を見せるか",
    verdict := .undecided,
    evidence := .questionOutsideModel "コードに取り下げの経路がない。status は creating と created だけで、コメントにある deleting と error は型にも代入にも無い。音声と台本は public/ の固定パスにあり、Firestore rules は書き込みを全て拒む。モデルには取り下げの操作が存在しない",
    industry := some (.gap "AI 音声の訂正告知の慣行は見つからない。Washington Post の AI 個人向け podcast は誤った引用を出し、訂正を出さなかった（報道、二次情報）。放送法 9 条の訂正放送は放送事業者の義務で、求めに応じて送る配信には及ばない") },
  { about := [coverImage, publishedShow],
    statement := "NDL サーチの書影 API が終わった後、本棚に表紙の画像を出すのか。出すなら、どこから、どの利用条件で取るのか",
    verdict := .undecided,
    evidence := .questionOutsideModel "外部のサービスの終了と利用条件の問題で、状態の遷移では示せない。コードは終了した API の URL を今も組み立てている",
    industry := some (.answered "NDL は JPRO の利用規約改定に伴い書影 API を 2026-03-31 に終了し、代わりの経路は示さず、書影は日本出版インフラセンター（JPO）に問い合わせるよう案内している") },
  { about := [keywordShow, userKeyword, broadcastSlot],
    statement := "キーワード番組は提供するのか。提供するなら、1 日 1 本の放送枠はキーワードごとか、全体で 1 本か",
    verdict := .undecided,
    evidence := .questionOutsideModel "キーワード番組の処理は pass で、登録キーワードを書き込む経路もない。到達できる状態が無いのでモデルでは示せない",
    industry := some (.answered "個人向けの日次音声は、話題ごとではなく利用者ごとに 1 日 1 本にまとめるのが主流（Google Daily Listen、Washington Post。二次情報）") }
]

def book : Book Term Ctx := { title := "advena 新刊ラジオ", terms, claims, stopScene := .modelled }

theorem book_check : book.check = true := by decide

end Glossary.Advena
