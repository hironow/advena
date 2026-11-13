import Glossary.Render

/-!
# The control experiment

Whether the comparison with a tool-less control (workflow step 5) was run is declared once, as
`control` in `Glossary/Registry.lean`. `just check` (control-check) verifies it:

- `.run`: at least one `experiments/<name>/` has `protocol.md` committed before `result.md`.
  The recipe checks that in git; this file only reports the declaration.
- `.skipped reason`: the reason is a real sentence (at least ten characters that are not spaces).
- `.undeclared`: allowed (the control is Tier 3); `status.py` lists it as not done.

The declaration reaches `status.py` and the grader through a machine line in
`docs/generated/summary.md`. Nothing is judged by words in files.

This file is the same for every domain. Do not edit it per project.
-/

namespace Glossary

def controlProblems : Control → List String
  | .skipped reason =>
    if meaningful reason then []
    else ["control is .skipped without a reason of at least ten characters"]
  | _ => []

/-- What `claims control` prints for the recipe: `run`, `skipped` or `undeclared`. -/
def controlWord : Control → String
  | .run => "run"
  | .skipped _ => "skipped"
  | .undeclared => "undeclared"

/-! ## Tests. They run on every `lake build`; a false one fails the build. -/

#guard (controlProblems .run).isEmpty
#guard (controlProblems .undeclared).isEmpty
#guard (controlProblems (.skipped "no time was left after Tier 2; the claims are unverified")).isEmpty
#guard (controlProblems (.skipped "n/a")).length == 1
#guard controlLine .run == "<!-- control: run -->"
#guard controlLine (.skipped "no time left") == "<!-- control: skipped; no time left -->"
#guard controlLine .undeclared == "<!-- control: undeclared -->"

end Glossary
