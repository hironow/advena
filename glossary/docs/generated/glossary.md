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

