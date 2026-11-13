<!-- 生成物。`just generate` が `Glossary/*.lean` から作る。手で編集しない。 -->

# 役割と停止の場面

共通の役割を、各用語に付けた役割から一覧にする。停止の場面について各用語集が宣言したことも載せる。宣言は `just check` (stop-check) が確かめる。

## Starter

<!-- stop-scene: ok; modelled -->
<!-- roles-tagged: 5 -->

停止の場面: 検査モデルにした。支える主張を下に載せる。

| 役割 | 用語 |
|---|---|
| 資源 (Resource) | Resource |
| 仮確保 (Hold) | Hold |
| 外部の確認 (External confirmation) | External confirmation |
| 権利 (Entitlement) | Entitlement |
| 停止 (Stop) | Emergency stop |
| 計画停止 (Planned stop) | なし |
| 期限 (Deadline) | なし |
| 代わりの経路 (Fallback channel) | なし |
| 供給の取り消し (Supply cancellation) | なし |
| 振替 (Reallocation) | なし |

### 停止についての主張

| 判定 | 主張 | 用語 | 証拠 |
|---|---|---|---|
| 証明済み | In the guarded design (issue only while the hold is alive), at most one customer is entitled to the resource, even across an emergency stop | Entitlement, Hold, External confirmation, Emergency stop | Quint + TLC 全状態: `Spec/starter.qnt` `guarded.exclusive` |
| 反例あり | In the guarded design, no confirmed customer is left with neither an entitlement nor a refund | External confirmation, Entitlement, Emergency stop | Quint 反例: `Spec/starter.qnt` `guarded.noOrphan` |
| 未決定 | How is a transaction resolved when its confirmation succeeds after the hold is gone? | External confirmation, Entitlement, Emergency stop | 業務側への質問。空白を示す反例: `Spec/starter.qnt` `guarded.noOrphan` |

## advena 新刊ラジオ

<!-- stop-scene: ok; in book Starter -->
<!-- roles-tagged: 4 -->

停止の場面: 次の用語集で検査モデルにした: Starter

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

