The source of truth is `Glossary/*.lean` (terms and claims) and `Spec/*.qnt` (models).
Run the `check` recipe before saying anything is done: `just check`, or `just <folder> check` when this project sits in a folder of a larger repository.

Authored by you: `Glossary/*.lean`, `Spec/*.qnt`, `Spec/tests.txt`, `README.md`, `docs/*.md`, `experiments/`.
Generated, never edited: `docs/generated/*.md`. To change them, edit `Glossary/*.lean` and run the `generate` recipe.
A hook refuses edits to `docs/generated/`, and `just check` fails when it does not match the glossaries.

Same for every domain, do not edit: every `Glossary/*.lean` except `Glossary/Registry.lean` and your own glossary files,
that is `Core.lean`, `Claim.lean`, `Render.lean`, `Progress.lean` and the rules `StopScene.lean`, `Questions.lean`, `Control.lean`;
also `Main.lean`, `justfile`, `.claude/hooks/`, `.githooks/`, and the `linter.extra` setting in `lakefile.toml`.
When a check fails, fix the glossary or the model, never the rule. `scripts/status.py` of the skill reports any difference from the template.
