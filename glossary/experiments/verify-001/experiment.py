"""verify-001: 道具なしのモデルは、読むだけで、番組制作モデルの変種が性質を守るかを当てられるか。

手順は protocol.md。リポジトリのルートから、順に実行する:

  uv run --no-project python -I glossary/experiments/verify-001/experiment.py variants
  uv run --no-project python -I glossary/experiments/verify-001/experiment.py truth
  uv run --no-project python -I glossary/experiments/verify-001/experiment.py sample
  uv run --no-project python -I glossary/experiments/verify-001/experiment.py selftest
  uv run --no-project python -I glossary/experiments/verify-001/experiment.py ask
  uv run --no-project python -I glossary/experiments/verify-001/experiment.py score

正解表、採点、対照の呼び出しは provable-glossary スキルの truth_table.py, replay_trace.py, run_control.py が行う。
この file が持つのは、変種の生成、出題の抽選、問いの文面、集計だけ。
"""

import argparse
import concurrent.futures
import itertools
import json
import pathlib
import random
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROJECT = HERE.parent.parent
SKILL_SCRIPTS = (
    pathlib.Path.home() / ".claude" / "skills" / "provable-glossary" / "scripts"
)
SPEC = PROJECT / "Spec" / "radio_show.qnt"
GEN = HERE / "gen"

SWITCHES = ["FIX_DAY", "FENCE", "TERMINAL", "SWEEP"]
# 性質ごとに、反例が出うる最小の規模で調べる (Glossary/Advena.lean の主張と同じ規模)
SIZES = {
    "single": ('Set("s1")', 'Set("r1", "r2")'),
    "pair": ('Set("s1", "s2")', 'Set("r1")'),
}
PROPERTIES = {
    "onePerDay": "pair",
    "sameRun": "single",
    "unchangedAfterPublish": "single",
    "dayAsIntended": "single",
    "oneProducerAtATime": "single",
    "noItemsNotFailed": "single",
}
MODELS = {
    "fable": "claude-fable-5-2",
    "opus": "claude-opus-5-5",
    "sonnet": "claude-sonnet-5-5",
}
SEED = 20261114
PER_VERDICT = 6
PER_PROPERTY = 3
ELIGIBLE_SHARE = 0.2

PROMPT = """次の Quint の仕様は、新刊紹介ラジオの番組制作の状態遷移モデルです。
道具は使わず、読んで考えるだけで答えてください。コードの実行やモデル検査はできません。

```quint
{spec}
```

問い: モジュール `{module}` で、`init` から `step` を繰り返して到達できるすべての状態で、不変条件 `{prop}` は成り立ちますか。

答え方:
- 成り立つなら verdict を "holds" にします。
- 破れるなら verdict を "violated" にして、`init` の後に実行する操作の列を trace に書きます。
  列の最後の操作の直後の状態で `{prop}` が偽になるようにします。各操作はその時点で実行可能でなければなりません。
- 操作の書き方 (引数は文字列、整数、true / false だけ):
  `collect("s1", 0, true, false)`, `deliver("s1", "r1")`, `check("r1")`, `writeScript("r1")`, `writeAudio("r1")`,
  `publish("r1")`, `depFails("r1")`, `ackTimeout("r1")`, `kill("r1")`, `leaseExpires("s1")`, `sweep("s1")`, `midnight`。

考えた後、最後に次の形の JSON を 1 つだけ、```json のコードブロックで出力してください。

```json
{{"verdict": "holds", "trace": []}}
```
"""


def base_module() -> str:
    """Spec/radio_show.qnt の先頭から module radio の終わりまで。scripted run と変種のモジュールは含めない。"""
    source = SPEC.read_text()
    start = source.index("\nmodule radio {")
    end = source.index("\n}\n", start) + 3
    return source[:end]


def variant_names() -> list[str]:
    return [
        "v" + "".join(bits) for bits in itertools.product("01", repeat=len(SWITCHES))
    ]


def variant_module(variant: str, size: str) -> str:
    shows, runs = SIZES[size]
    switches = ", ".join(
        f"{name} = {'true' if bit == '1' else 'false'}"
        for name, bit in zip(SWITCHES, variant[1:])
    )
    return f"module {size} {{\n  import radio({switches},\n               SHOWS = {shows}, RUNS = {runs}).*\n}}\n"


def variant_path(variant: str) -> pathlib.Path:
    return GEN / f"{variant}.qnt"


def skill(script: str, *args: str, timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "uv",
            "run",
            "--no-project",
            "--quiet",
            "python",
            str(SKILL_SCRIPTS / script),
            *args,
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def cmd_variants() -> None:
    GEN.mkdir(exist_ok=True)
    base = base_module()
    for variant in variant_names():
        modules = "\n".join(variant_module(variant, size) for size in SIZES)
        variant_path(variant).write_text(base + "\n" + modules)
    print(f"variants: {len(variant_names())} files in {GEN.relative_to(PROJECT)}")


def cmd_truth() -> None:
    rows = []
    for variant in variant_names():
        for size in SIZES:
            props = [p for p, s in PROPERTIES.items() if s == size]
            out = GEN / f"truth-{variant}-{size}.tsv"
            res = skill(
                "truth_table.py",
                str(PROJECT),
                "--spec",
                str(variant_path(variant).relative_to(PROJECT)),
                "--modules",
                size,
                "--properties",
                ",".join(props),
                "--out",
                str(out),
                "--timeout",
                "900",
                timeout=3600,
            )
            if res.returncode != 0:
                sys.exit(f"truth: {variant} {size} failed\n{res.stdout}\n{res.stderr}")
            for cell in read_tsv(out):
                rows.append(
                    (
                        variant,
                        cell["module"],
                        cell["property"],
                        cell["verdict"],
                        cell["distinct_states"],
                    )
                )
            print(f"truth: {variant} {size} done", flush=True)
    lines = ["variant\tmodule\tproperty\tverdict\tdistinct_states"] + [
        "\t".join(r) for r in rows
    ]
    (HERE / "truth.tsv").write_text("\n".join(lines) + "\n")


def read_tsv(path: pathlib.Path) -> list[dict[str, str]]:
    header, *body = path.read_text().splitlines()
    names = header.split("\t")
    return [dict(zip(names, line.split("\t"))) for line in body]


def cmd_sample() -> None:
    truth = read_tsv(HERE / "truth.tsv")
    total = len(variant_names())
    eligible = []
    for prop in PROPERTIES:
        cells = [r for r in truth if r["property"] == prop]
        held = sum(r["verdict"] == "holds" for r in cells)
        if min(held, total - held) >= ELIGIBLE_SHARE * total:
            eligible.extend(cells)
    rng = random.Random(SEED)
    rng.shuffle(eligible)
    chosen: list[dict[str, str]] = []
    for row in eligible:
        same_verdict = sum(c["verdict"] == row["verdict"] for c in chosen)
        same_prop = sum(c["property"] == row["property"] for c in chosen)
        if same_verdict < PER_VERDICT and same_prop < PER_PROPERTY:
            chosen.append(row)
    lines = ["item\tvariant\tmodule\tproperty\ttruth"] + [
        f"{i:02d}\t{r['variant']}\t{r['module']}\t{r['property']}\t{r['verdict']}"
        for i, r in enumerate(chosen, 1)
    ]
    (HERE / "items.tsv").write_text("\n".join(lines) + "\n")
    print(f"sample: {len(chosen)} items from {len(eligible)} eligible cells")


def prompt_for(item: dict[str, str]) -> str:
    spec = base_module() + "\n" + variant_module(item["variant"], item["module"])
    return PROMPT.format(spec=spec, module=item["module"], prop=item["property"])


def replay(item: dict[str, str], trace: list) -> bool:
    res = skill(
        "replay_trace.py",
        str(PROJECT),
        "--spec",
        str(variant_path(item["variant"]).relative_to(PROJECT)),
        "--module",
        item["module"],
        "--property",
        item["property"],
        "--trace",
        json.dumps(trace),
        timeout=600,
    )
    return res.returncode == 0


# 既知の反例: 現行コード (v0000) で、ack 期限後の再配信が台本を上書きする (code1 の mixedScriptAndAudioTest)
KNOWN_TRACE = [
    'collect("s1", 0, true, false)',
    'deliver("s1", "r1")',
    'check("r1")',
    'writeScript("r1")',
    'ackTimeout("r1")',
    'deliver("s1", "r2")',
    'check("r2")',
    'writeScript("r2")',
    'writeAudio("r1")',
    'publish("r1")',
]


def cmd_selftest() -> None:
    res = skill(
        "replay_trace.py",
        str(PROJECT),
        "--spec",
        str(variant_path("v0000").relative_to(PROJECT)),
        "--module",
        "single",
        "--property",
        "sameRun",
        "--trace",
        json.dumps(KNOWN_TRACE),
        "--self-test",
        timeout=1200,
    )
    print(res.stdout.strip())
    holds_item = {"variant": "v1111", "module": "single", "property": "sameRun"}
    rejected = not replay(holds_item, KNOWN_TRACE)
    print(
        ("ok  " if rejected else "NG  ")
        + "the same trace is rejected where sameRun holds (v1111)"
    )
    if res.returncode != 0 or not rejected:
        sys.exit(1)


def cmd_ask() -> None:
    items = read_tsv(HERE / "items.tsv")
    prompts = GEN / "prompts"
    prompts.mkdir(parents=True, exist_ok=True)
    jobs = []
    for item in items:
        path = prompts / f"{item['item']}.txt"
        path.write_text(prompt_for(item))
        for name, model in MODELS.items():
            jobs.append((name, model, item["item"], path))

    def ask(job: tuple[str, str, str, pathlib.Path]) -> str:
        name, model, number, path = job
        out = HERE / "answers" / name / f"{number}.md"
        res = skill(
            "run_control.py",
            "--model",
            model,
            "--prompt-file",
            str(path),
            "--out",
            str(out),
            "--effort",
            "high",
            "--timeout",
            "2400",
            timeout=2700,
        )
        return f"{name} {number} exit={res.returncode} {res.stdout.strip()} {res.stderr.strip()[-200:]}"

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for line in pool.map(ask, jobs):
            print(line, flush=True)


JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def parse_answer(text: str) -> tuple[str, list]:
    blocks = JSON_BLOCK.findall(text)
    if not blocks:
        return "none", []
    try:
        answer = json.loads(blocks[-1])
    except json.JSONDecodeError:
        return "none", []
    verdict = answer.get("verdict", "none")
    trace = answer.get("trace", [])
    return (verdict if verdict in ("holds", "violated") else "none"), (
        trace if isinstance(trace, list) else []
    )


def cmd_score() -> None:
    items = read_tsv(HERE / "items.tsv")
    rows = ["model\titem\tproperty\ttruth\tanswer\treplay\tcorrect"]
    totals: dict[str, int] = {}
    for name in MODELS:
        for item in items:
            path = HERE / "answers" / name / f"{item['item']}.md"
            verdict, trace = (
                parse_answer(path.read_text()) if path.exists() else ("none", [])
            )
            replayed = "-"
            if verdict == "violated":
                replayed = "confirmed" if replay(item, trace) else "rejected"
            correct = (
                verdict == "holds" and item["truth"] == "holds"
            ) or replayed == "confirmed"
            totals[name] = totals.get(name, 0) + int(correct)
            rows.append(
                "\t".join(
                    [
                        name,
                        item["item"],
                        item["property"],
                        item["truth"],
                        verdict,
                        replayed,
                        "1" if correct else "0",
                    ]
                )
            )
    (HERE / "scores.tsv").write_text("\n".join(rows) + "\n")
    for name, total in totals.items():
        print(f"score: {name} {total}/{len(items)}")


def main() -> None:
    commands = {
        "variants": cmd_variants,
        "truth": cmd_truth,
        "sample": cmd_sample,
        "selftest": cmd_selftest,
        "ask": cmd_ask,
        "score": cmd_score,
    }
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("command", choices=commands)
    commands[parser.parse_args().command]()


if __name__ == "__main__":
    main()
