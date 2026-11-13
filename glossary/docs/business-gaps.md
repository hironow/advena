# 業界との比較と、業務の判断

調べた日: 2026-11-14。質問の分類は用語集にあり、一覧は [generated/questions.md](generated/questions.md) です。
ここには、分類の根拠と出典を書きます。

## 結論

1. **「その日の本」の意味が、NDL のデータと合っていない見込みが高い。** 発売日は `dcterms:issued` にあり、コードが比べている `pubDate` は発売日より前の時刻つきの日時でした。言明「毎日出版される書籍」を守るには、選び方を変えるか、言明を変える必要があります。
2. **「1 日 1 本」と「重複しても 1 回分」は、業界でも GCP でも答えが決まっている。** Podcast では、直した回は同じ GUID のまま差し替えます。GCP は、Scheduler も Eventarc も重複がありうるとして、冪等な受け手を求めています。advena のコードは、この前提に立っていません。
3. **制作に失敗した日、空の日、公開後の訂正は、業界に決まった答えがない**（空白）。Washington Post の AI 個人向け podcast では、聴取者が影響を受けた例があります。
4. **書影 API はすでに終了している。** コードは今もその URL を組み立てています。
5. 形式手法が役に立つのは、2 の「重複しても 1 回分」を設計で保証するところです。1、3、4 は業務とデータの判断で、モデルでは決められません。

## 調べ方と確かさ

3 つの領域に分け、調査のサブエージェントを並行に送りました（GCP の配信の意味、日次の自動生成音声の慣行、NDL のフィードの日付）。
結論が拠る点は、私が一次資料を開いて確かめました。表の「確認」の列がそれです。
「二次」は、サブエージェントの報告や報道だけで、私が一次資料を開けなかった点です。
NDL サーチは調査の途中から 429（アクセス過多）を返したので、advena が実際に使う `rss/ndls/bib.xml` は開けていません。

## 質問ごとの根拠

### 「その日の本」は発売日か、記録の日か（答えあり）

| 点 | 出典 | 確かさ |
|---|---|---|
| ISBN 9784198663346 の記録で `pubDate` は 2026-11-01 18:34 +0900、`dcterms:issued` は 2026-12-11、説明は「発売」 | NDL サーチ OpenSearch API の応答（2026-11-14 取得） | 確認（取得したファイルを読んだ） |
| JPRO のデータには「近日中に刊行される図書のメタデータ（近刊情報）」が入る | NDL サーチ API 仕様 付録 1（2026-06-24 版） | 確認（取得した PDF の本文） |
| OpenSearch の `from` は「開始出版年月日」で、出版日で絞り込める | NDL サーチ API 仕様 v1.5（2026-09-25） | 確認（同上） |
| `pubDate` の定義 | NDL の文書に見つからない | 未確認 |
| advena の使う `bib.xml` でも同じ意味か | 開けなかった（429） | 未確認 |

コードの例（`book.py` の docstring）でも `pubDate` は「Sat, 21 Dec 2024 18:46:00 +0900」のように時刻つきで、記録の時刻らしい値です。

### 同じ日の再実行（答えあり）

- Apple Podcasts: 「All episodes must contain a globally unique identifier (GUID), which never changes.」「Apple Podcasts will ignore duplicate `<enclosure>` URLs.」（https://podcasters.apple.com/support/823-podcast-requirements 、確認）。重複した回は削除されうる、という規約 §1.9 は二次（ページが 404）。
- Cloud Scheduler: 「Cloud Scheduler provides at-least-once delivery.」「Duplicate job requests for the same scheduled run can occur.」「Your targets should be idempotent.」（https://docs.cloud.google.com/scheduler/docs/overview 、確認）。重複の原因の一つに、応答が attemptDeadline を超えることが挙がっています。収集実行は最大 1000 件の書誌を 0.1 秒ずつ待ちながら取るので、長くかかりえます。attemptDeadline の既定値 3 分は二次。

### 制作に失敗した日（空白）

- 失敗した日の扱いを公表した日次の自動生成音声は見つかりませんでした。Spotify Daily Drive の更新漏れの苦情はコミュニティの投稿にあります（二次）。
- GCP 側の事実（確認）: Pub/Sub は ack 期限が過ぎると再送し（https://docs.cloud.google.com/pubsub/docs/push 「If you send a negative acknowledgment or the acknowledgment deadline expires, Pub/Sub resends the message.」）、dead letter に回すまでの試行回数の既定は 5 回で、それより少なく回すこともある（https://docs.cloud.google.com/pubsub/docs/handling-failures ）。dead letter トピックに購読が無いと、移したメッセージは失われる（二次: サンプルのコメント）。

### 番組の日付（答えあり）

- 日次ニュース番組の題名の日付は放送枠の日付で、`pubDate` は公開の時刻です。NHK ラジオニュースの RSS では、題名「ニュース 2026年11月14日午前00時00分」に `pubDate` 「Sat, 14 Nov 2026 00:10:00 +0900」が付いていました（二次: サブエージェントが RSS を読んだ）。

### 空の日（空白）

- 空の日の指針は見つかりませんでした。日次ニュース番組は別の回で枠を埋める例がありました（二次）。
- Alexa の Flash Briefing は、7 日より古い項目を無視します（Amazon の Feed Reference の検索結果の抜粋。ページは開いていない）。

### LLM と TTS を呼ぶ回数（答えあり）

- Eventarc: 「Because of at-least-once delivery, your event handler might receive duplicate events.」「It's a best practice to design your handlers to be idempotent.」「you should use the event ID as the idempotency key.」（https://docs.cloud.google.com/eventarc/docs/retry-events 、確認）
- Cloud Run: 既定のタイムアウトは 300 秒、上限 3600 秒。「Closing the connection doesn't terminate the container instance.」「The container might continue processing the aborted request」（https://docs.cloud.google.com/run/docs/configuring/request-timeout 、確認）。ack 期限も 300 秒なので、制作が 5 分を超えると、最初の実行が動いたまま再配信が届きます。

### 同時の初回サインイン（答えあり。ただし仕組みは書かれていない）

- 「Cloud Firestore guarantees serializable isolation of transactions.」（https://firebase.google.com/docs/firestore/transaction-data-contention 、確認）
- 同じページが説明するロックは「transactions place locks on the documents they read」のように文書単位で、検索結果が空の場合にどう守るかは書かれていません。直列化可能の保証を文字どおり取れば、利用者文書は 2 つできません（`accountGuarded`）。

### 公開後の訂正と取り下げ（空白）

- 放送法 第 2 条第 1 号: 「放送」とは「公衆によつて直接受信されることを目的とする電気通信…の送信」。第 9 条第 1 項: 訂正放送は放送事業者の義務で、真実でないと判明した日から 2 日以内（e-Gov 法令 API、確認）。求めに応じて送るインターネットの配信は放送に当たらない、という総務省資料の記述は二次。
- Washington Post の AI 個人向け podcast は、誤った引用を出し、注意書きを足して続け、訂正は出さなかった（2025-12、NPR などの報道。二次）。
- Apple は AI で作った音声を、各回と番組のメタデータで目立つように示すことを求める（規約 §1.11。二次、ページが 404）。

### 書影（答えあり）

- 「書影画像を提供する書影APIは、データ提供機関である出版情報登録センター（JPRO）の利用規約改定に伴い、2026年3月31日（火）をもってサービスを終了しました。」（https://ndlsearch.ndl.go.jp/news/20260401_thumbnail 、確認）

### キーワード番組（答えあり）

- 個人向けの日次音声は、話題ごとではなく利用者ごとに 1 日 1 本にまとめるのが主流です（Google Daily Listen、Washington Post。二次）。

## 分類ごとにわかること

- **答えあり**: 重複は「1 回分にまとめる」が業界と GCP の共通の前提です。advena の現行コードの反例（1 日 2 本、台本と音声の混線）は、この前提に反します。日付は「枠の日付」が慣行で、制作した日ではありません。
- **問われていない**: 該当なし。
- **空白**: 失敗した日、空の日、訂正。どれも聴取者に見える判断で、決めるのは運用者です。

## 形式手法では閉じられない空白

公開後の訂正と取り下げです。何を誤りとみなし、誰が決め、聴取者に何を見せるかは、状態の遷移ではなく編集の判断です。モデルが言えるのは「今のコードには取り下げの経路がない」ことだけです。

## 業務の判断の一覧

| 判断 | 聴取者にとっての価値 | 形式手法の役割 |
|---|---|---|
| 「その日の本」を発売日で選ぶか、言明を「新しく登録された本」に変えるか | 番組の内容が説明どおりになる | なし（データの意味の問題） |
| 同じ日の再実行を差し替えにする（1 日 1 本） | 同じ日に 2 本並ばない | 方針案の条項 1 が全状態で守ることを TLC で確認。道具なしの対照も読むだけで同じ判定をした |
| 公開した台本と音声を同じ制作のものにする | 台本表示と音声が食い違わない | 方針案の条項 2 が全状態で守ることを TLC で確認。対照も同じ判定をした |
| 失敗した日を failed として残し、知らせる | 番組が無い理由がわかる | 方針案の条項 4 で「いずれ終わる」を TLC で確認（時相性質は対照実験の対象外）。何を見せるかは業務の判断 |
| 空の日に何を見せるか | 「壊れた」と「新刊がない」を区別できる | 条項 3 で skipped を failed と分けることを TLC で確認。対照も同じ判定をした。見せ方は業務の判断 |
| 公開後の訂正・取り下げの経路を持つ | 誤った紹介を正せる | なし |
| 書影を別の経路で取るか、出さないか | 本棚が壊れて見えない | なし |
| AI で作った音声だと各回で示す | 聴取者が性質を知って聞ける | なし |

形式手法の役割を書いた行は、対照実験 [verify-001](../experiments/verify-001/) と比べました。対照は 12 問すべてに正解したので、役割は「全状態での保証」であって、読むだけではわからないことの発見ではありません（[findings.md](findings.md)）。

## 主な出典

- Pub/Sub push: https://docs.cloud.google.com/pubsub/docs/push
- Pub/Sub dead letter: https://docs.cloud.google.com/pubsub/docs/handling-failures
- Eventarc の再試行: https://docs.cloud.google.com/eventarc/docs/retry-events
- Cloud Run のタイムアウト: https://docs.cloud.google.com/run/docs/configuring/request-timeout
- Cloud Scheduler: https://docs.cloud.google.com/scheduler/docs/overview
- Firestore のトランザクション: https://firebase.google.com/docs/firestore/transaction-data-contention
- Apple Podcasts の要件: https://podcasters.apple.com/support/823-podcast-requirements
- NDL サーチ 書影 API の終了: https://ndlsearch.ndl.go.jp/news/20260401_thumbnail
- NDL サーチ API 仕様: https://ndlsearch.ndl.go.jp/file/help/api/specifications/ndlsearch_api_20260925.pdf と付録 1（ndlsearch_api_ap1_20260624.pdf）
- 放送法（e-Gov 法令検索）: https://laws.e-gov.go.jp/law/325AC0000000132
