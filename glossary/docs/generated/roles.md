<!-- 生成物。`just generate` が `Glossary/*.lean` から作る。手で編集しない。 -->

# 役割と停止の場面

共通の役割を、各用語に付けた役割から一覧にする。停止の場面について各用語集が宣言したことも載せる。宣言は `just check` (stop-check) が確かめる。

## advena 新刊ラジオ

<!-- stop-scene: ok; modelled -->
<!-- roles-tagged: 4 -->

停止の場面: 検査モデルにした。支える主張を下に載せる。

| 役割 | 用語 |
|---|---|
| 資源 (Resource) | 放送枠 |
| 仮確保 (Hold) | なし |
| 外部の確認 (External confirmation) | 文書作成イベント |
| 権利 (Entitlement) | 公開済み番組 |
| 停止 (Stop) | 制作の中断 |
| 計画停止 (Planned stop) | なし |
| 期限 (Deadline) | なし |
| 代わりの経路 (Fallback channel) | なし |
| 供給の取り消し (Supply cancellation) | なし |
| 振替 (Reallocation) | なし |

### 停止についての主張

| 判定 | 主張 | 用語 | 証拠 |
|---|---|---|---|
| 反例あり | 現行コードでは、制作が中断して再配信が JST の 0 時をまたいでも、公開済み番組は本来の日（broadcasted_at、無ければ収集した日）の番組である | 制作の中断, 番組対象日, 再配信, 公開済み番組 | Quint 反例: `Spec/radio_show.qnt` `code1.dayAsIntended` |
| 反例あり | 現行コードでは、番組を進める操作が公平に実行されるなら、制作の中断が何度起きても、作成された番組はいずれ公開などの終わりの状態に至る | 制作の中断, 配信打ち切り, 該当なし, 制作待ち | Quint + TLC 反例: `Spec/radio_show.qnt` `code1.Liveness` |
| 証明済み | 提案（番組対象日を作成時に固定して保存し、その日から文書の ID を作る、ほか 3 点）では、中断や 0 時またぎがあっても、1 つの番組対象日に公開済み番組は高々 1 本（番組 2 つ、実行枠 1 つ） | 放送枠, 番組対象日, 収集実行, 制作の中断 | Quint + TLC 全状態: `Spec/radio_show.qnt` `proposal2.onePerDay` |
| 証明済み | 提案（status の確認をトランザクションにして制作権を世代つきで取り、台本と音声を世代ごとのパスに書き、世代が一致するときだけ公開する、ほか 3 点）では、公開済み番組の台本と音声は同じ制作実行が書いたもの（番組 1 つ、実行枠 2 つ） | 公開済み番組, 番組台本, 番組音声, 再配信, 制作の中断 | Quint + TLC 全状態: `Spec/radio_show.qnt` `proposal1.sameRun` |
| 証明済み | 提案では、制作が中断して再配信が JST の 0 時をまたいでも、公開済み番組は本来の日の番組である（番組 1 つ、実行枠 2 つ） | 制作の中断, 番組対象日, 公開済み番組 | Quint + TLC 全状態: `Spec/radio_show.qnt` `proposal1.dayAsIntended` |
| 証明済み | 提案では、番組を進める操作（配信、制作の各段階、リースの期限切れ、回収処理）が公平に実行されるなら、制作の中断が何度起きても、作成された番組はいずれ公開・skipped・failed のどれかになる（番組 1 つ、実行枠 2 つ） | 制作の中断, 配信打ち切り, 該当なし, 制作待ち | Quint + TLC 全状態: `Spec/radio_show.qnt` `proposal1.Liveness` |
| 反例あり | 提案から回収処理だけを除いても、作成された番組はいずれ終わりの状態に至る | 制作の中断, 配信打ち切り, 制作待ち | Quint + TLC 反例: `Spec/radio_show.qnt` `noSweep1.Liveness` |
| 反例あり | 提案から日付の固定だけを除いても、0 時をまたいだ再配信の後の公開済み番組は本来の日の番組である（番組 1 つ、実行枠 2 つ） | 番組対象日, 制作の中断, 公開済み番組 | Quint 反例: `Spec/radio_show.qnt` `noFixDay1.dayAsIntended` |
| 未決定 | 制作が失敗した日（配信打ち切り）の番組をどうするか。諦めるのか、遅れて作るのか、誰がいつ気づき、聴取者に何を見せるのか | 制作の中断, 配信打ち切り, 放送枠 | 業務側への質問。空白を示す反例: `Spec/radio_show.qnt` `code1.Liveness`, `Spec/radio_show.qnt` `noSweep1.Liveness` |
| 未決定 | broadcasted_at の無い番組の日付は、収集した日か、制作した日か。遅れて制作したとき、どちらの日の本を紹介するのか | 番組対象日, 制作の中断, 収集実行 | 業務側への質問。空白を示す反例: `Spec/radio_show.qnt` `code1.dayAsIntended` |

