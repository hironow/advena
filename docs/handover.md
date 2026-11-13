# Handover

**Last updated:** 2026-11-14 03:13 (JST)
**Updated by:** Claude Code セッション e2d899b2-9707-476e-a005-b20c1c67fa9e

## Current State

PR #218（検証可能な用語集 `glossary/`）は、2026-11-14 に develop へ merge commit `006b638` として入った。
その commit への push で走った Test、Format、Glossary、Build and Push はすべて success だった。
ルートの `just check` は、workflow の検査、frozen install、format、frontend と backend のテスト、`just glossary check` を走らせる（2026-11-14 にローカルで exit 0）。
アプリのコード（`backend/`、`frontend/`、`scripts/`）は #218 で変えていない。
`docs/intent.md` はまだ無い。

## In Progress

なし。

## Next Actions

1. 次の work unit の intent を持ち主が決め、`/intent-handover-governance` で `docs/intent.md` に書き取る。候補は「Known Risks」の 3 件。
2. intent が「1 日 2 本」の修正なら、まず失敗するテストを書く [Red]。
   - 場所: `backend/genai/tests/test_main.py`。
   - 内容: `/async_task`（kind=latest_all）を同じ日に 2 回呼ぶと、`radio_shows` に creating の文書が 2 つできることを示す。
   - 作法: CI=true では `db` が MockFirestore になる（`backend/genai/src/database/firestore.py:9`）。RSS、OAI-PMH、GCS の呼び出しは、既存のテストと同じく monkeypatch で置き換える。
   - 確認: `just backend-test` が赤になる。
   - 直し方の候補: `glossary/docs/production-policy.md` の条項 1。
3. 書影が表示されないかを画面で確かめる。
   - 手順: `mr f:emulator`、`mr be:dev`、`mr fe:dev` の順に起動し、本棚を開く。
   - 理由: NDL の書影 API は 2026-03-31 に終了している。URL を作っているのは `backend/genai/src/book/book.py:33`。

## Known Risks / Blockers

- **「その日の本」が業務の言明と違う見込み。**
  - 待ち: 持ち主の判断（2026-11-14 から）。
  - 内容: 制作は RSS の `pubDate` で本を選ぶが、NDL の記録では発売日は `dcterms:issued` にあった。確かめたのは 2 件で、advena が使う `bib.xml` は未確認。
  - 緩和: 用語集の質問として残してある（`glossary/docs/generated/questions.md`）。
- **1 日 2 本の公開と、台本と音声の混線（モデル上の反例で、実装では未再現）。**
  - 緩和: Next Actions 2 でテストにする。手順は `glossary/docs/findings.md` の「限界」節。
- **書影が出ない見込み（画面では未確認）。**
  - 緩和: Next Actions 3。

## Context the Next Actor Needs

- anchor の付いた宣言（例 `def latest_all`）の名前を変えたり消したりすると、`just glossary check` と CI の Glossary が落ちる。直すのは `glossary/Glossary/Advena.lean` の anchor と定義の方。
- `glossary/docs/generated/` は手で編集しない。Claude Code のフックが拒む。作り直すのは `just glossary generate`。
- この clone は `core.hooksPath=.githooks` にしてある。pre-commit が `just glossary generated-check` を走らせる。
- ルートの `just check` には elan、Java 17 以上、bun、uv が要る。モデル検査だけで数分かかる。
- 用語集を続けるときは `/provable-glossary` スキルを使い、まず `python3 ~/.claude/skills/provable-glossary/scripts/status.py .` を実行する。

## Relevant Files and Commands

- `glossary/README.md` — 用語集の入口。わかったこと、限界、規則の例外
- `glossary/docs/findings.md` — 反例、実装で再現する手順、モデルの限界
- `glossary/docs/production-policy.md` — 修正案の 4 条項と検査結果
- `just check` — 全言語のローカルゲート
- `just glossary check` / `just glossary generate` — 用語集の検査と、生成文書の作り直し
- `just install-json2ts check-generated` — 生成された entity の型の確認
