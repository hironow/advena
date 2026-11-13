# advena の検証可能な用語集

advena（新刊紹介の AI ラジオ）の業務用語と、それについての主張を集めたものです。
各主張には証拠が 1 つずつ付き、判定は次の 3 つのどれかです。

- **証明済み**: Lean の証明、または TLC がモデルの全状態を調べて成り立った。
- **反例あり**: Lean で否定を証明した、または Quint / TLC が反例を見つけた。
- **未決定**: 業務側への質問。モデルが空白を示す反例か、モデルでは示せない理由が付く。

件数は [docs/generated/summary.md](docs/generated/summary.md) にあります。

- 開始点: B（実装があり、用語集がない）。用語はコードから起こしました。
- 到達した段階: Tier 3（業界との比較、道具なしのモデルとの対照実験、方針案の検査）。
- 読んだコード: `backend/genai/src`、`frontend/web`（`lib/`、`auth.ts`、`firestore.rules`）、`scripts/`、`docs/zenn-article.md`。commit `b9978c5`（develop）の時点です。
- 既存の実装は変えていません。

## 役割の対応

役割の表は [docs/generated/roles.md](docs/generated/roles.md) です（用語に付けた役割から生成）。表に出ない注意:

- **資源**の「放送枠」は、業務上の言明（1 日 1 回のみ）だけにあります。コードにこの枠を守る確認はありません。
- **外部の確認**は決済ではなく、Eventarc が届ける文書作成イベントです。少なくとも 1 回届き、重複も遅延もあり、アプリには止められません。
- **停止**は緊急停止ではなく「制作の中断」です。依存先（Gemini、Cloud Text-to-Speech、GCS）の失敗や、Cloud Run の打ち切りで起きます。止まっている間も再配信と時刻は進みます。
- **仮確保**と**期限**はありません。制作待ち（creating）に期限はなく、過去の番組も一覧に残ります。これ自体が所見です。

## わかったこと

1. **紹介する本の選び方が、言明と違う可能性が高い。** 制作は RSS の `pubDate` が当日の項目を選びます。NDL の同じ記録を見ると、`pubDate` は発売日ではなく、それより前の時刻つきの日時でした（発売日は `dcterms:issued`）。「その日に出版された本」ではなく「その日に記録が登録・更新された本」を紹介している見込みです。
2. **現行コードは「1 日 1 本」を守らない。** 収集実行は呼ばれるたびに新しい番組を作ります。Cloud Scheduler は同じ予定を重複して実行しうると公式に書いています。
3. **公開された台本と音声が、別々の制作実行のものになりうる。** ack 期限（300 秒）を過ぎた後の再配信を別のインスタンスが受けると、2 つの制作が同じパスに上書きします。公開後に音声が変わる場合もあります。
4. **creating が 4 つの状況を兼ねている。** 配信待ち、制作中、該当なしで終わった、配信が打ち切られた、の 4 つです。後の 2 つは二度と進みませんが、誰も気づけません（Lean で証明）。
5. **4 つの規則でこれらを閉じられる**（モデルの中で確認。コードは変えていない）。どの 1 つを外しても、別の性質が破れます。詳しくは [docs/production-policy.md](docs/production-policy.md) にあります。

対照実験では、道具を持たない 3 つのモデルも、変種が性質を守るかを読むだけで 12 問すべて当てました。この用語集で形式手法が加えたのは、到達できる全状態での**保証**であり、読むだけではわからないことの発見ではありません（[docs/findings.md](docs/findings.md)）。

## 読む順番

1. この README
2. [docs/generated/glossary.md](docs/generated/glossary.md): 用語と定義、コードの場所
3. [docs/findings.md](docs/findings.md): 何を調べ、何がわかり、どこまで言えるか
4. [docs/generated/questions.md](docs/generated/questions.md): 業務側への質問と、業界での扱い
5. [docs/business-gaps.md](docs/business-gaps.md): 業界調査の根拠と、業務の判断の一覧
6. [docs/production-policy.md](docs/production-policy.md): 番組制作の方針案と、その検査
7. [experiments/verify-001/](experiments/verify-001/): 対照実験の記録

## 使い方

リポジトリのルートで実行します。

```sh
just glossary setup      # 外部の Lean パッケージは使わないので、何も取得しない
just glossary check      # 証明、モデル検査、生成文書の鮮度、コードの anchor をすべて確かめる
just glossary generate   # docs/generated/ を用語集から作り直す
```

ルートの `just check` も `glossary::check` を含みます。CI では `.github/workflows/glossary.yaml` が同じ検査を走らせます。

必要なもの: elan（Lean 4.35.0 を `lean-toolchain` から取得）、bun（Quint 0.33.1 を `bunx` で実行）、Java 17 以上（TLC）、just、ripgrep、git、uv。

## 書くものと生成されるもの

| 種類 | 場所 | 書き手 |
|---|---|---|
| 用語、主張、証明、コードの anchor | `Glossary/Advena.lean` | 人 |
| 状態機械モデル | `Spec/radio_show.qnt`、`Spec/account.qnt`、`Spec/tests.txt` | 人 |
| 分析の文書 | `README.md`、`docs/*.md` | 人 |
| 実験の記録 | `experiments/verify-001/` | 人。対照の回答（`answers/`）は実行記録で、書き換えない |
| 生成文書 | `docs/generated/*.md` | `just glossary generate` だけ |
| 共通の仕組み | `Glossary/` の `Advena.lean` と `Registry.lean` 以外、`Main.lean`、`mod.just` | 誰も変えない（provable-glossary スキルのテンプレートと同じ） |

生成文書は 3 つの仕組みで守られています。

1. `just glossary check` の generated-check が作り直して比べ、手での編集、追加、削除を拒みます。
2. Claude Code のフック（`.claude/hooks/protect_generated.py`）が、`docs/generated/` への編集を実行前に拒みます。
3. git の pre-commit フック（`.githooks/pre-commit`、`core.hooksPath=.githooks`）が、ずれたままのコミットを止めます。

## 置き場所

- `Glossary/Advena.lean`: 用語、Lean の証明（creating の多義性、番組対象日が制作時刻で変わること）、主張と質問
- `Spec/radio_show.qnt`: 番組制作。現行コード（`code1`、`code2`）、提案（`proposal1`、`proposal2`）、提案から 1 点ずつ除いた変種
- `Spec/account.qnt`: 同じ人の 2 つの初回サインイン
- `experiments/verify-001/`: 対照実験

## AGENTS.md の規則からの例外

リポジトリの規則（新しいコードは Go、Python は uv で実行）から外れるものが 4 つあります。どれもリポジトリの持ち主が承認しました（2026-11-14）。

1. 仕様の記述としての Lean と Quint。
2. テンプレートに付いてくる Lean の実行ファイル `claims`（生成文書と anchor の一覧を出す）。
3. テンプレートに付いてくる Python のフック。起動は `uv run --no-project python -I` にしてあります。
4. 対照実験の手順 `experiments/verify-001/experiment.py`（標準ライブラリだけ。uv で実行）。

## 限界

- モデルは小さい: JST の日付 2 日、番組 1〜2 つ、制作実行の枠 1〜2 つ、再配信 2 回まで（Pub/Sub の既定は 5 回）。各主張に規模を書いています。
- 反例は「コードのモデル」に対するものです。実装では再現していません。再現の手順は [docs/findings.md](docs/findings.md) に書きました。
- GCP の設定値（ack 期限 300 秒など）は `scripts/` の値です。本番の実際の設定は確かめていません。
- 提案はモデルの中にだけあります。業務を知る人のレビューを受けていません。
- 業界調査は 2026-11-14 時点です。一次資料で確かめた点と二次情報を [docs/business-gaps.md](docs/business-gaps.md) で分けています。
