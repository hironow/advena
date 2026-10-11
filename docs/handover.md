# Handover

Updated: 2026-10-11

Dependencies use the official npm and PyPI registries. The Bun lockfile keeps
its package versions and integrity hashes. PR workflows skip drafts and run
when marked ready. Existing image publication still follows pushes to develop
and main.

`just check` runs workflow validation, frozen installs, format checks, and both
test suites. `just install-json2ts check-generated` checks generated entity types.
