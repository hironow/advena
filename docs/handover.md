# Handover

Updated: 2026-11-14

Dependencies use the official npm and PyPI registries. The Bun lockfile keeps
its package versions and integrity hashes. PR workflows skip drafts and run
when marked ready. Existing image publication still follows pushes to develop
and main.

`just check` runs workflow validation, frozen installs, format checks, both
test suites, and the glossary gate (`just glossary check`). `just
install-json2ts check-generated` checks generated entity types.

## Glossary (branch feat/provable-glossary, not pushed)

`glossary/` holds a machine-checked glossary of the radio show: terms anchored
to the code, Lean proofs, Quint models of the code as it is and of a proposed
production policy. Read `glossary/README.md` first. The code itself was not
changed.

Open risks nobody has committed to yet:

- The show picks books by the RSS `pubDate`, which in NDL's data is not the
  release date (`glossary/docs/business-gaps.md`). The stated rule "books
  published that day" is probably not what the show does.
- The NDL cover-image API that `book.thumbnail()` points to ended on
  2026-03-31. Bookshelf covers are probably broken (not checked on screen).
- The current code can publish two shows for one day and a script and audio
  from different production runs (`glossary/docs/findings.md`). These are
  model counterexamples, not reproduced against the implementation.
- `.github/workflows/glossary.yaml` has not run on GitHub yet; it needs a push.
