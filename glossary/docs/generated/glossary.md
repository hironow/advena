<!-- 生成物。`just generate` が `Glossary/*.lean` から作る。手で編集しない。 -->

# 用語と主張

## Starter

### 用語

| 用語 | ID | 文脈 | 定義 | 定義依存 | 関連 |
|---|---|---|---|---|---|
| Customer | `customer` | sales | A party that wants the resource |  | Hold |
| Resource | `resource` | sales | Something limited that cannot be given to two customers at once |  |  |
| Hold | `hold` | sales | A time-limited reservation of the resource for one customer | Customer, Resource |  |
| External confirmation | `externalConfirmation` | external | A result produced outside the system; it cannot be stopped and may arrive late | Customer |  |
| Entitlement | `entitlement` | sales | The hard-to-revoke right to the resource, issued to a customer | Customer, Resource, External confirmation |  |
| Emergency stop | `emergencyStop` | operations | The system autonomously stops accepting new holds and new confirmations | Hold, External confirmation |  |

### 主張

| 判定 | 主張 | 用語 | 証拠 |
|---|---|---|---|
| 証明済み | The glossary has unique IDs, no dangling references, and no circular definitions | Customer, Resource, Hold, Entitlement | Lean: `Glossary.Starter.terms_wellFormed` |
| 反例あり | In the naive design (issue on confirmation alone), at most one customer is entitled to the resource | Entitlement, Hold, External confirmation | Quint 反例: `Spec/starter.qnt` `naive.exclusive` |
| 証明済み | In the guarded design (issue only while the hold is alive), at most one customer is entitled to the resource, even across an emergency stop | Entitlement, Hold, External confirmation, Emergency stop | Quint + TLC 全状態: `Spec/starter.qnt` `guarded.exclusive` |
| 反例あり | In the guarded design, no confirmed customer is left with neither an entitlement nor a refund | External confirmation, Entitlement, Emergency stop | Quint 反例: `Spec/starter.qnt` `guarded.noOrphan` |
| 未決定 | How is a transaction resolved when its confirmation succeeds after the hold is gone? | External confirmation, Entitlement, Emergency stop | 業務側への質問。空白を示す反例: `Spec/starter.qnt` `guarded.noOrphan` |

## advena 新刊ラジオ

### 用語

| 用語 | ID | 文脈 | 定義 | 定義依存 | 関連 |
|---|---|---|---|---|---|
| 新着書誌フィード | `ndlFeed` | collection | 国立国会図書館サーチが提供する新着書誌の RSS。latest_all(size) が URL を組み立て、fetch_rss が 300 秒のタイムアウトで取得する。取得した XML は GCS の private/rss/ にキャッシュする |  |  |
| フィード項目 | `feedItem` | collection | 新着書誌フィードの 1 項目。タイトル、要約、リンク、ISBN または JP-e コード、項目日時を持つ | 新着書誌フィード |  |
| 項目日時 | `itemDate` | collection | フィード項目の published。RSS が付けた日時で、書籍の発売日と同じ意味かは確かめていない。split_books が JST の日付に直して番組対象日と比べ、過去・当日・未来に分ける。未来の区分があるので、フィードには取得日より後の日付の項目も入りうる | フィード項目 |  |
| 書誌メタデータ | `bibMetadata` | collection | ISBN または JP-e コードで OAI-PMH から取る書誌情報。private/oai_pmh/ にキャッシュする | フィード項目 |  |
| 結合マスタデータ | `masterdata` | collection | 1 回の収集で得たフィード項目と書誌メタデータを結合した JSON。ファイル名は RSS の lastBuildDate から作り、private/masterdata/ に置く。番組文書はこのパスを持ち、制作実行はここから項目を選ぶ | フィード項目, 書誌メタデータ |  |
| 収集実行 | `collectionRun` | collection | POST /async_task（kind=latest_all）で始まる処理。フィードと書誌を取り込み、結合マスタデータを書き、最後に制作待ちの番組文書を 1 つ作る。呼ばれるたびに新しい文書を作り、同じ日の文書が既にあるかは確かめない。起動元は Cloud Scheduler とされるが、ジョブの設定はリポジトリにない | 新着書誌フィード, 結合マスタデータ | 番組文書, 過去日指定の収集 |
| 番組対象日 | `broadcastDay` | production | その番組で紹介する本を選ぶ JST の日付。番組文書に broadcasted_at があればその日、無ければ制作実行を始めた時刻の JST 日付になる（exec_date_jst）。項目日時がこの日付に等しい項目だけを紹介する。公開時に broadcasted_at として書き戻され、一覧の並び順に使われる | 項目日時 | 制作実行, 番組文書 |
| 放送枠 | `broadcastSlot` | publication | 番組対象日 1 日につき 1 本だけ番組を公開できる、という枠。業務上の言明（docs/zenn-article.md「ラジオ番組の提供は1日1回のみです」）による。コードにはこの枠を守る確認がない | 番組対象日 |  |
| 番組文書 | `radioShow` | production | Firestore の radio_shows コレクションの 1 文書。収集実行が status=creating で作り、制作実行が公開する。ID は新しい UUID で、番組対象日からは決まらない | 結合マスタデータ |  |
| 制作待ち | `showCreating` | production | 番組文書の status が creating の状態。配信を待っている、制作中、該当なしで配信が終わった後、配信が打ち切られた後、の 4 つの状況を区別しない。一覧には出ない | 番組文書 |  |
| 文書作成イベント | `docCreatedEvent` | delivery | Firestore の文書作成を Eventarc が Pub/Sub の push で /add_radio_show に届けるもの。少なくとも 1 回届き、重複も遅延もある。アプリは届くのを止められない。購読の ack 期限は 300 秒（scripts の設定値。本番の実設定は確かめていない） | 番組文書 |  |
| 再配信 | `redelivery` | delivery | 応答が成功でないか、ack 期限（300 秒）までに返らないとき、Pub/Sub が同じイベントをもう一度届けること。間隔は 300〜600 秒（scripts の設定値）。前の制作実行がまだ動いていても再配信は起きる | 文書作成イベント |  |
| 配信打ち切り | `deadLetter` | delivery | 再配信が上限回数に達したイベントを dead letter トピックに移すこと。上限回数は scripts で指定しておらず Pub/Sub の既定値に従う。dead letter の購読は手動で作るとされ、番組文書の状態を変える処理はない | 再配信 |  |
| 番組台本 | `showScript` | production | LLM の応答の <script> ブロックにある読み上げ文。public/radio_show_script/{番組文書の ID}.txt に保存し、公開 URL で配る。同じ番組の制作実行は同じパスに上書きする | 番組文書 |  |
| 番組音声 | `showAudio` | production | 番組台本を Cloud Text-to-Speech（ja-JP-Neural2-B、MP3）で読み上げた音声。public/radio_show_audio/{番組文書の ID}.mp3 に上書き保存する | 番組台本 |  |
| 制作実行 | `productionRun` | production | 文書作成イベント 1 回分の処理。/add_radio_show が status を読み、created なら 204 で終える。そうでなければ番組対象日の項目を選び、LLM で台本を作って保存し、音声を作って保存し、公開する。status の確認と公開は別々の書き込みで、その間を守る排他はない。uvicorn の 1 プロセスが、イベントループを止めたまま同期に実行する | 文書作成イベント, 番組文書, 番組対象日, 番組台本, 番組音声 |  |
| 該当なし | `noItemsDay` | production | 番組対象日に項目日時が一致する項目が 0 件のこと。制作実行はログを残して戻り、/add_radio_show は 204 を返すので配信は成功で終わり、番組文書は制作待ちのまま残る。業務上の言明は「新規出版がない日は提供されません」 | 番組対象日, 制作実行, 制作待ち |  |
| 公開済み番組 | `publishedShow` | publication | status が created の番組文書。番組音声と番組台本の公開 URL、紹介した本、番組対象日を持ち、サインインした全聴取者に一覧で見える。取り下げる手段はコードにない | 番組文書, 番組台本, 番組音声, 番組対象日 |  |
| 制作の中断 | `productionHalt` | operations | 制作実行が途中で止まること。依存先（Gemini、Cloud Text-to-Speech、GCS）の失敗で例外になって 500 を返す場合と、Cloud Run のリクエストやインスタンスが打ち切られる場合がある。どちらも再配信に回る。止まっている間も、再配信の回数と時刻（番組対象日を制作時刻で決める場合はその日付）は進む | 制作実行, 再配信 |  |
| 過去日指定の収集 | `staffRerun` | operations | 運用者が /async_task に broadcasted_at を付けて呼び、過去の日の番組文書を作ること。radio_show.py のコメントが想定している。その日の番組が既にあっても作れる | 収集実行, 番組対象日 |  |
| 聴取者 | `listener` | account | 許可されたドメインかメールアドレスの Google アカウントでサインインした人。公開済み番組の一覧を読める |  |  |
| 利用者文書 | `userDoc` | account | users コレクションの 1 文書。サインイン時に firebase_uid で探し、無ければトランザクションの中で status=creating、version 0 で作る。/add_user が created にする。Python 側で読み出すときの移行（版 0 から 1）も creating を created に変える | 聴取者 |  |
| 登録キーワード | `userKeyword` | account | users/{id}/keywords の文書。データの型はあるが、書き込む経路はコードにない（Firestore rules も write: false） | 利用者文書 |  |
| キーワード番組 | `keywordShow` | publication | 登録キーワードで絞った番組。業務上は予定だが未実装で、/async_task の kind=latest_with_keywords_by_user は何もしない | 登録キーワード, 公開済み番組 |  |
| 状態の命名規約 | `statusConvention` | production | フロントのコメントにある規約。-ing は command、-ed は event として Eventarc で backend に通知する。creating、created、deleting、error を挙げるが、型にあるのは creating と created だけで、deleting と error を代入する箇所もない | 番組文書, 利用者文書 |  |

### 主張

| 判定 | 主張 | 用語 | 証拠 |
|---|---|---|---|
| 証明済み | 用語集は、ID が一意で、参照先が存在し、定義が循環していない | フィード項目, 結合マスタデータ, 番組文書, 公開済み番組, 制作実行 | Lean: `Glossary.Advena.terms_wellFormed` |
| 反例あり | 現行コードでは、番組文書の status だけで、その番組がまだ公開に向けて進むのか、もう誰も扱わないのかを判別できる（status の写しと、コードから分けた 5 つの状況についての主張） | 制作待ち, 該当なし, 配信打ち切り, 制作実行 | Lean (否定を証明): `Glossary.Advena.creating_is_overloaded` |
| 反例あり | 現行コードでは、番組対象日は番組文書だけで決まり、いつ制作しても同じ日になる（番組対象日の決め方の写しについての主張） | 番組対象日, 番組文書, 制作実行 | Lean (否定を証明): `Glossary.Advena.day_depends_on_production_time` |
| 未決定 | 公開済み番組を訂正または取り下げる手段を持つべきか。持つなら、誰が決め、聴取者に何を見せるか | 公開済み番組, 状態の命名規約 | 業務側への質問。モデルで示せない理由: コードに取り下げの経路がない。status は creating と created だけで、コメントにある deleting と error は型にも代入にも無い。音声と台本は public/ の固定パスにあり、Firestore rules は書き込みを全て拒む。モデルには取り下げの操作が存在しない |
| 未決定 | キーワード番組は提供するのか。提供するなら、1 日 1 本の放送枠はキーワードごとか、全体で 1 本か | キーワード番組, 登録キーワード, 放送枠 | 業務側への質問。モデルで示せない理由: キーワード番組の処理は pass で、登録キーワードを書き込む経路もない。到達できる状態が無いのでモデルでは示せない |

