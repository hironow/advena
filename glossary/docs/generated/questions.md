<!-- 生成物。`just generate` が `Glossary/*.lean` から作る。手で編集しない。 -->

# 業務側への質問

判定が「未決定」の主張の一覧である。業務を知る人が決める。

## Starter

<!-- questions: 1; with-counterexample: 1; outside-model: 0 -->
<!-- industry: classified: 0; researched: 0 -->

| # | 質問 | 用語 | 根拠 | 業界 |
|---|---|---|---|---|
| 1 | How is a transaction resolved when its confirmation succeeds after the hold is gone? | External confirmation, Entitlement, Emergency stop | 業務側への質問。空白を示す反例: `Spec/starter.qnt` `guarded.noOrphan` | 未分類 |

## advena 新刊ラジオ

<!-- questions: 2; with-counterexample: 0; outside-model: 2 -->
<!-- industry: classified: 0; researched: 0 -->

| # | 質問 | 用語 | 根拠 | 業界 |
|---|---|---|---|---|
| 1 | 公開済み番組を訂正または取り下げる手段を持つべきか。持つなら、誰が決め、聴取者に何を見せるか | 公開済み番組, 状態の命名規約 | 業務側への質問。モデルで示せない理由: コードに取り下げの経路がない。status は creating と created だけで、コメントにある deleting と error は型にも代入にも無い。音声と台本は public/ の固定パスにあり、Firestore rules は書き込みを全て拒む。モデルには取り下げの操作が存在しない | 未分類 |
| 2 | キーワード番組は提供するのか。提供するなら、1 日 1 本の放送枠はキーワードごとか、全体で 1 本か | キーワード番組, 登録キーワード, 放送枠 | 業務側への質問。モデルで示せない理由: キーワード番組の処理は pass で、登録キーワードを書き込む経路もない。到達できる状態が無いのでモデルでは示せない | 未分類 |

