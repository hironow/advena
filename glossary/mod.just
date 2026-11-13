# Provable glossary. `just check` is the only entry point for checks.
# This file is the same for every domain. Do not edit it per project.

# The Quint version is pinned in the file `quint-version`, as Lean's is in `lean-toolchain`.
# By default Quint runs through bunx at exactly that version, so nothing has to be installed.
# To use an installed binary instead, set QUINT (for example QUINT=quint); its version must match.
quint_version := trim(read("quint-version"))
quint := env("QUINT", "bunx @informalsystems/quint@" + quint_version)
seed := "0x5eed"

# List the tasks
default:
    @just --list

# Run once. Fetches a prebuilt cache only if the project added mathlib; otherwise there is nothing to fetch.
setup:
    #!/usr/bin/env bash
    set -euo pipefail
    if rg -q '"name": *"mathlib"' lake-manifest.json 2>/dev/null; then
      lake exe cache get
    else
      echo "setup: no external Lean packages; nothing to fetch"
    fi

# Every check
check: lean-check stop-check question-check control-check spec-check generated-check anchor-check migration-check skill-check

# Lean: build the proofs. Reject warnings, sorry, and extra axioms.
lean-check:
    #!/usr/bin/env bash
    set -euo pipefail
    if rg -n '\b(sorry|native_decide)\b|^\s*(axiom|unsafe)\b' Glossary Main.lean Audit.lean; then
      echo "lean-check: sorry / native_decide / axiom / unsafe are not allowed" >&2
      exit 1
    fi
    lake build --wfail
    audit="$(lake env lean Audit.lean)"
    echo "$audit"
    if echo "$audit" | rg -q 'sorryAx|ofReduceBool|trustCompiler'; then
      echo "lean-check: a proof depends on an untrusted axiom" >&2
      exit 1
    fi

# Every registered glossary declares its stop scene, and the declaration agrees with its terms and
# claims (Glossary/StopScene.lean). Reads only the glossary, never words in files.
stop-check:
    lake exe claims stop

# Every question rests on counterexamples that show the gap, or says why no model can show it
# (Glossary/Questions.lean). Reads only the glossary.
question-check:
    lake exe claims questions

# The control declaration (Glossary/Registry.lean). For .run, some experiments/<name>/ must have
# protocol.md committed before result.md: the procedure was fixed before the result was known.
control-check:
    #!/usr/bin/env bash
    set -euo pipefail
    declared="$(lake exe claims control)"
    echo "control-check: the control is declared $declared"
    [[ "$declared" == run ]] || exit 0
    found=0
    for protocol in experiments/*/protocol.md; do
      [[ -f "$protocol" ]] || continue
      result="${protocol%protocol.md}result.md"
      [[ -f "$result" ]] || continue
      p="$(git log --diff-filter=A --format=%H -- "$protocol" | tail -n 1)"
      r="$(git log --diff-filter=A --format=%H -- "$result" | tail -n 1)"
      if [[ -n "$p" && -n "$r" && "$p" != "$r" ]] && git merge-base --is-ancestor "$p" "$r"; then
        echo "control-check: $(dirname "$protocol"): protocol.md was committed before result.md"
        found=1
      fi
    done
    [[ $found == 1 ]] || { echo "control-check: the control is declared .run, but no experiments/<name>/ has protocol.md committed before result.md" >&2; exit 1; }

# Quint: typecheck, run the scripted tests (each line of Spec/tests.txt), then check every claim in the glossaries.
spec-check:
    #!/usr/bin/env bash
    set -euo pipefail
    # Run TLC through Quint. Another verification on this machine can still hold Apalache's port, and a run
    # can end without a verdict; wait and retry. A real error (a type error) still fails after the retries.
    verify() {
      local out rc n
      for n in 1 2 3 4 5; do
        out="$({{quint}} verify --backend tlc "$@" 2>&1)" && rc=0 || rc=$?
        # Finished with a verdict: done. No verdict (a busy port, a dropped connection): ask again.
        if rg -q '^\[(ok|violation)\]' <<<"$out" && ! rg -q 'Address already in use' <<<"$out"; then break; fi
        sleep $((n * 3))
      done
      printf '%s\n' "$out"
      return "$rc"
    }
    actual="$({{quint}} --version)"
    if [[ "$actual" != "{{quint_version}}" ]]; then
      echo "spec-check: quint {{quint_version}} is required (found $actual)" >&2
      exit 1
    fi
    for f in Spec/*.qnt; do
      {{quint}} typecheck "$f"
    done
    while IFS=' ' read -r file main; do
      [[ -z "$file" || "$file" == \#* ]] && continue
      # Several samples: a scripted run that passes through a random choice then fails every time, not once in a while.
      {{quint}} test --max-samples=20 --main="$main" "$file"
    done < Spec/tests.txt
    # Several claims may cite the same check as evidence; run each distinct check once.
    claims="$(lake exe claims gate | awk '!seen[$0]++')"
    [[ -n "$claims" ]] || { echo "spec-check: the list of claims is empty" >&2; exit 1; }
    while IFS=$'\t' read -r expect kind file main property; do
      case "$kind" in
        invariant) flag="--invariant=$property" ;;
        temporal) flag="--temporal=$property" ;;
        *) echo "spec-check: unknown kind '$kind'" >&2; exit 1 ;;
      esac
      case "$expect/$kind" in
        holds/*)
          # TLC explores every reachable state.
          out="$(verify --main="$main" "$flag" "$file")" \
            || { echo "$out" | tail -30; echo "FAIL holds $main.$property" >&2; exit 1; }
          echo "$out" | rg -q '^\[ok\]' \
            || { echo "$out" | tail -30; echo "FAIL holds $main.$property" >&2; exit 1; }
          states="$(echo "$out" | rg -o '[0-9]+ distinct states found' | tail -1 || true)"
          echo "ok  holds     $main.$property ($states)"
          ;;
        violated/invariant)
          # The simulator looks for a counterexample without a script. It is fast but shallow, so
          # when it finds none, TLC searches every reachable state before the claim is rejected.
          out="$({{quint}} run --main="$main" "$flag" --seed={{seed}} \
            --max-samples=20000 --max-steps=20 "$file" 2>&1)" && rc=0 || rc=$?
          if [[ "$rc" -ne 0 ]] && echo "$out" | rg -q '\[violation\]'; then
            echo "ok  violated  $main.$property"
          else
            out="$(verify --main="$main" "$flag" "$file")" && rc=0 || rc=$?
            if [[ "$rc" -eq 0 ]] || ! echo "$out" | rg -q '^\[violation\]'; then
              echo "$out" | tail -30
              echo "FAIL violated $main.$property: no counterexample found by the simulator or by TLC" >&2
              exit 1
            fi
            echo "ok  violated  $main.$property (found by TLC; too deep for the simulator)"
          fi
          ;;
        violated/temporal)
          # TLC finds counterexamples to liveness.
          out="$(verify --main="$main" "$flag" "$file")" && rc=0 || rc=$?
          if [[ "$rc" -eq 0 ]] || ! echo "$out" | rg -q '^\[violation\]'; then
            echo "$out" | tail -30
            echo "FAIL violated $main.$property: no counterexample found" >&2
            exit 1
          fi
          echo "ok  violated  $main.$property (temporal)"
          ;;
        *)
          echo "spec-check: unknown expectation '$expect'" >&2
          exit 1
          ;;
      esac
    done <<<"$claims"

# Rebuild the generated documents (docs/generated/) from the glossaries, and drop any that are no longer generated.
# Never edit them by hand.
generate:
    lake exe claims docs docs/generated

# The generated documents match the glossaries. Rejects edited, added, and removed files.
generated-check:
    #!/usr/bin/env bash
    set -euo pipefail
    fresh="$(mktemp -d)"
    trap 'rm -rf "$fresh"' EXIT
    lake exe claims docs "$fresh"
    diff -ru docs/generated "$fresh" \
      || { echo "generated-check: docs/generated does not match the glossaries. Do not edit it; run 'just generate'" >&2; exit 1; }

# Every code anchor of a term still resolves: the file exists and contains the text.
# Anchors are written `path#text` with the path taken from the repository root. `!path#text` asserts that the text is absent.
anchor-check:
    #!/usr/bin/env bash
    set -euo pipefail
    # The repository root: the top of the git work tree, unless that tree ignores this folder.
    root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
    if git -C "$root" check-ignore -q "$(pwd)" 2>/dev/null; then root="$(pwd)"; fi
    fail=0
    count=0
    while IFS=$'\t' read -r term anchor; do
      [[ -z "$term" ]] && continue
      count=$((count + 1))
      absent=0
      if [[ "$anchor" == '!'* ]]; then absent=1; anchor="${anchor:1}"; fi
      path="${anchor%%#*}"
      needle="${anchor#*#}"
      if [[ "$anchor" != *"#"* || -z "$needle" ]]; then
        echo "anchor-check: $term: write the anchor as path#text, got '$anchor'" >&2; fail=1; continue
      fi
      if [[ ! -f "$root/$path" ]]; then
        echo "anchor-check: $term: no such file: $path" >&2; fail=1; continue
      fi
      if [[ "$absent" -eq 1 ]]; then
        if rg -qF -- "$needle" "$root/$path"; then
          echo "anchor-check: $term: '$needle' now occurs in $path, and the definition says it does not" >&2; fail=1
        fi
      else
        rg -qF -- "$needle" "$root/$path" \
          || { echo "anchor-check: $term: '$needle' no longer occurs in $path" >&2; fail=1; }
      fi
    done < <(lake exe claims anchors)
    [[ "$fail" -eq 0 ]] && echo "anchor-check: $count anchors resolve"
    exit "$fail"

# During a migration from an existing glossary: every legacy term is mapped to a term here or retired with a reason.
# Reads migration/legacy.tsv (term, definition) and migration/mapping.tsv (term, mapped|retired, term ID or reason).
# Does nothing when there is no migration/ folder.
migration-check:
    #!/usr/bin/env bash
    set -euo pipefail
    [[ -f migration/legacy.tsv ]] || exit 0
    [[ -f migration/mapping.tsv ]] || { echo "migration-check: migration/mapping.tsv is missing" >&2; exit 1; }
    ids="$(lake exe claims terms)"
    fail=0
    total=0
    while IFS=$'\t' read -r term _rest; do
      [[ -z "$term" || "$term" == "term" ]] && continue
      total=$((total + 1))
      row="$(awk -F'\t' -v t="$term" '$1 == t' migration/mapping.tsv | head -1)"
      if [[ -z "$row" ]]; then
        echo "migration-check: legacy term not accounted for: $term" >&2; fail=1; continue
      fi
      status="$(cut -f2 <<<"$row")"
      target="$(cut -f3 <<<"$row")"
      case "$status" in
        mapped)
          grep -qxF -- "$target" <<<"$ids" \
            || { echo "migration-check: '$term' is mapped to '$target', which is not a term ID" >&2; fail=1; } ;;
        retired)
          [[ -n "$target" ]] || { echo "migration-check: '$term' is retired without a reason" >&2; fail=1; } ;;
        *)
          echo "migration-check: '$term' has status '$status'; use mapped or retired" >&2; fail=1 ;;
      esac
    done < migration/legacy.tsv
    [[ "$fail" -eq 0 ]] && echo "migration-check: $total legacy terms accounted for"
    exit "$fail"

# Run generated-check in git's pre-commit hook
install-hooks:
    git config core.hooksPath .githooks

# Only where this repository holds the source of the provable-glossary skill: refresh the skill's copies
skill-sync:
    #!/usr/bin/env bash
    set -euo pipefail
    [[ -f skills/sync.py ]] || { echo "skill-sync: no skill source here"; exit 0; }
    python3 -I skills/sync.py write

# Only where this repository holds the source of the provable-glossary skill: copy it into a checkout of the skills repository
skill-export repo:
    #!/usr/bin/env bash
    set -euo pipefail
    [[ -f skills/sync.py ]] || { echo "skill-export: no skill source here"; exit 0; }
    python3 -I skills/sync.py export "{{repo}}"

# Only where this repository holds the source of the provable-glossary skill: the copies are up to date
skill-check:
    #!/usr/bin/env bash
    set -euo pipefail
    [[ -f skills/sync.py ]] || exit 0
    python3 -I skills/sync.py check
