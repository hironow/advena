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
  | ndlFeed | feedItem | itemDate | bibMetadata | masterdata | collectionRun
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
    gloss := "フィード項目の published。RSS が付けた日時で、書籍の発売日と同じ意味かは確かめていない。split_books が JST の日付に直して番組対象日と比べ、過去・当日・未来に分ける。未来の区分があるので、フィードには取得日より後の日付の項目も入りうる",
    defDeps := [feedItem],
    anchors := ["backend/genai/src/book/feed.py#published_parsed = feed.get(\"published_parsed\")",
                "backend/genai/src/event_sourcing/workflows.py#future[link] = mst_book"] },
  { id := bibMetadata, label := "書誌メタデータ", context := .collection,
    gloss := "ISBN または JP-e コードで OAI-PMH から取る書誌情報。private/oai_pmh/ にキャッシュする",
    defDeps := [feedItem],
    anchors := ["backend/genai/src/book/oai_pmh.py#def get_metadata_by_isbn",
                "backend/genai/src/book/oai_pmh.py#def get_metadata_by_jp_e_code"] },
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
  { about := [publishedShow, statusConvention],
    statement := "公開済み番組を訂正または取り下げる手段を持つべきか。持つなら、誰が決め、聴取者に何を見せるか",
    verdict := .undecided,
    evidence := .questionOutsideModel "コードに取り下げの経路がない。status は creating と created だけで、コメントにある deleting と error は型にも代入にも無い。音声と台本は public/ の固定パスにあり、Firestore rules は書き込みを全て拒む。モデルには取り下げの操作が存在しない" },
  { about := [keywordShow, userKeyword, broadcastSlot],
    statement := "キーワード番組は提供するのか。提供するなら、1 日 1 本の放送枠はキーワードごとか、全体で 1 本か",
    verdict := .undecided,
    evidence := .questionOutsideModel "キーワード番組の処理は pass で、登録キーワードを書き込む経路もない。到達できる状態が無いのでモデルでは示せない" }
]

-- 停止の場面は、自分のモデルが入るまで starter が担う。モデルを入れたらこの行を置き換える。
def book : Book Term Ctx := { title := "advena 新刊ラジオ", terms, claims, stopScene := .inBook "Starter" }

theorem book_check : book.check = true := by decide

end Glossary.Advena
