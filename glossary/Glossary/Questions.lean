import Glossary.Render

/-!
# Every question states its basis

An undecided claim is a question for the business. `just check` (question-check) runs
`questionProblems` on every registered book: each question must rest on counterexamples that show
the gap (`.question [...]`, not empty) or say why no model can show it
(`.questionOutsideModel "<reason>"`, a reason of at least ten characters). An industry
classification, where present, says what was found, and only questions carry one. The rule reads the
glossary only, never words in files.

This file is the same for every domain. Do not edit it per project.
-/

namespace Glossary

def questionProblems (books : List BookView) : List String :=
  books.flatMap fun b =>
    let qs := b.claims.filter (·.verdict == .undecided)
    let basis := (qs.zipIdx.filter fun (c, _) => !c.basisOk).map fun (c, i) =>
      s!"{b.title}: question {i + 1} (\"{c.statement}\") has no basis. Give it the counterexamples that show the gap (.question [...]), or say why no model can show it (.questionOutsideModel \"<reason>\")"
    let notes := (qs.zipIdx.filter fun (c, _) => !(c.industry.all (·.noteOk))).map fun (c, i) =>
      s!"{b.title}: question {i + 1} (\"{c.statement}\") is classified against the industry without saying what was found (a note of at least ten characters)"
    let stray := (b.claims.filter fun c => c.verdict != .undecided && c.industry.isSome).map fun c =>
      s!"{b.title}: \"{c.statement}\" is not a question but carries an industry classification"
    basis ++ notes ++ stray

/-! ## Tests. They run on every `lake build`; a false one fails the build. -/

namespace QuestionsTest

def claim (verdict : Verdict) (basisOk : Bool) (industry : Option Industry := none) : ClaimRow :=
  { verdict, statement := "q", about := "", aboutIds := [], evidence := "", quint := false,
    witnessed := false, basisOk, industry }

def book (claims : List ClaimRow) : BookView :=
  { title := "B", terms := [], claims, gate := [], stopScene := .undeclared }

#guard (questionProblems [book [claim .undecided true, claim .proved true]]).isEmpty
#guard (questionProblems [book [claim .undecided true, claim .undecided false]]).length == 1
-- The problem names the question by its number among the questions.
#guard ((questionProblems [book [claim .undecided true, claim .undecided false]]).head!.splitOn "question 2").length == 2
-- Only questions are judged here; other claims carry their own evidence.
#guard (questionProblems [book [claim .proved false]]).isEmpty
-- Not classified yet: allowed (Tier 1); the grader and status.py count it as unclassified.
#guard (questionProblems [book [claim .undecided true]]).isEmpty
-- Classified against the industry, with a note on what was found.
#guard (questionProblems [book [claim .undecided true (some (.gap "no operator settles this in its terms"))]]).isEmpty
#guard (questionProblems [book [claim .undecided true (some .notResearched)]]).isEmpty
-- A classification that says nothing.
#guard (questionProblems [book [claim .undecided true (some (.answered "n/a"))]]).length == 1
-- Only questions are classified.
#guard (questionProblems [book [claim .proved true (some (.notAsked "cinemas do not rebook at all"))]]).length == 1

end QuestionsTest

end Glossary
