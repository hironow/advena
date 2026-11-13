import Glossary.Core

/-!
# Claims and evidence

Every claim in a glossary carries exactly one piece of evidence.
- Lean evidence holds the proof itself as a value. Without a proof this file does not compile.
- Quint evidence names a spec file, a module, and an invariant. `just check` runs that list as it is.
- An undecided claim is a question for the domain experts.

This file is the same for every domain. Do not edit it per project.
-/

namespace Glossary

/-- Where a Quint invariant lives. -/
structure QuintRef where
  file : String
  main : String
  invariant : String
  /-- Whether this is a temporal (liveness) property. If false, it is an invariant. -/
  temporal : Bool := false

inductive Evidence where
  /-- Proved in Lean. -/
  | lean (name : String) (prop : Prop) (proof : prop)
  /-- The negation is proved in Lean. -/
  | leanRefutes (name : String) (prop : Prop) (proof : ¬ prop)
  /-- Holds in every reachable state of the model, checked by Quint + TLC. -/
  | holds (ref : QuintRef)
  /-- The Quint simulator finds a counterexample. -/
  | violated (ref : QuintRef)
  /-- A question for the business to decide, with the counterexamples that show the gap.
  The list must not be empty: a question no model can show uses `questionOutsideModel`. -/
  | question (witnesses : List QuintRef)
  /-- A question for the business that no model shows, with the reason (a legal deadline, an
  organisational decision, a state nothing in the code reaches). -/
  | questionOutsideModel (reason : String)

/-- How the industry handles a question (workflow step 6). Each kind but `notResearched` carries a
note on what was found; the sources go in the authored comparison document. -/
inductive Industry where
  /-- The industry has a settled answer. -/
  | answered (note : String)
  /-- The industry does not face this question at all. -/
  | notAsked (note : String)
  /-- No settled answer, and customers are affected: a candidate for a policy draft. -/
  | gap (note : String)
  /-- Not looked at yet. -/
  | notResearched

def Industry.researched : Industry → Bool
  | .notResearched => false
  | _ => true

inductive Verdict where
  | proved | counterexample | undecided
  deriving DecidableEq, Repr

structure Claim (ι : Type) where
  about : List ι
  statement : String
  verdict : Verdict
  evidence : Evidence
  /-- For a question: how the industry handles it. Leave it out until the comparison (Tier 2). -/
  industry : Option Industry := none

def Evidence.verdict : Evidence → Verdict
  | .lean .. => .proved
  | .holds .. => .proved
  | .leanRefutes .. => .counterexample
  | .violated .. => .counterexample
  | .question .. => .undecided
  | .questionOutsideModel .. => .undecided

def Evidence.isQuint : Evidence → Bool
  | .holds .. | .violated .. => true
  | _ => false

/-- What a book says about the stop scene: what happens to work in flight when the system stops
(pattern 4). `just check` (stop-check) verifies the declaration against the terms and claims. -/
inductive StopScene where
  /-- Not declared yet. `just check` fails until the book declares one of the others. -/
  | undeclared
  /-- The scene is modelled: a term has role `.stop`, and the claims about it include a
  counterexample, a proved result, and Quint evidence. -/
  | modelled
  /-- Nothing is in flight across a stop. Accepted only when no term has the role
  `externalConfirmation`, `hold`, `entitlement` or `deadline`. -/
  | waived (reason : String)
  /-- Another book of this project, named by its title, models the scene. -/
  | inBook (title : String)

/-- Whether the comparison with a tool-less control (workflow step 5) was run. Declared once, as
`control` in `Glossary/Registry.lean`; `just check` (control-check, `Glossary/Control.lean`) verifies it. -/
inductive Control where
  /-- Not declared yet. Allowed: the control is Tier 3. -/
  | undeclared
  /-- Run: some `experiments/<name>/` has `protocol.md` committed before `result.md`. -/
  | run
  /-- Skipped, with the reason. The documents say which statements are therefore unverified. -/
  | skipped (reason : String)

/-- A glossary together with the claims made about it. -/
structure Book (ι κ : Type) where
  title : String
  terms : List (Entry ι κ)
  claims : List (Claim ι)
  stopScene : StopScene := .undeclared

variable {ι κ : Type} [DecidableEq ι]

/-- A reason worth reading: at least ten characters that are not spaces. -/
def meaningful (s : String) : Bool := (s.toList.filter (fun c => !c.isWhitespace)).length ≥ 10

/-- A classification states what was found, unless it says the question was not researched. -/
def Industry.noteOk : Industry → Bool
  | .answered note | .notAsked note | .gap note => meaningful note
  | .notResearched => true

/-- Every question says what it rests on: counterexamples that show the gap, or a reason why no
model can show it. -/
def Evidence.basisOk : Evidence → Bool
  | .question ws => !ws.isEmpty
  | .questionOutsideModel reason => meaningful reason
  | _ => true

/-- Claims mention only terms in the glossary, and each verdict matches its kind of evidence.
Whether every question states its basis (`Evidence.basisOk`) is checked by `just check`
(question-check, `Glossary/Questions.lean`), which can name the question. -/
def Book.claimsCheck (b : Book ι κ) : Bool :=
  b.claims.all fun c =>
    c.about.all (fun t => decide (t ∈ ids b.terms)) && decide (c.evidence.verdict = c.verdict)

def Book.check (b : Book ι κ) : Bool := Glossary.check b.terms && b.claimsCheck

/-! ## Tests. They run on every `lake build`; a false one fails the build. -/

namespace ClaimTest

def ref : QuintRef := { file := "Spec/a.qnt", main := "m", invariant := "p" }

-- A question backed by a counterexample.
#guard (Evidence.question [ref]).basisOk
-- A question outside every model, with the reason.
#guard (Evidence.questionOutsideModel "the legal deadline is in no model").basisOk
-- A question with neither a counterexample nor a reason.
#guard !(Evidence.question []).basisOk
-- A reason that says nothing.
#guard !(Evidence.questionOutsideModel "n/a").basisOk

end ClaimTest

end Glossary
