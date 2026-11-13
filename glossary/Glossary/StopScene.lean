import Glossary.Render

/-!
# The stop scene

Every project says what happens to work in flight when the system stops (pattern 4 in the skill).
Each book declares it in `stopScene`, and `just check` (stop-check) runs `stopProblems` on every
registered book. The rule reads only the glossary: the roles tagged on terms and the claims with
their verdicts and kinds of evidence. It never looks at words in files.

- `.modelled`: some term has role `.stop`, and the claims about such terms include a
  counterexample, a proved result, and at least one Quint check.
- `.waived reason`: the reason has at least ten characters, and no term has a role that can be in
  flight across a stop (`inFlightRoles`).
- `.inBook title`: another registered book with that title declares `.modelled`.
- `.undeclared`: always a problem.

This file is the same for every domain. Do not edit it per project.
-/

namespace Glossary

/-- The roles whose work can be half done when the system stops. -/
def inFlightRoles : List Role := [.externalConfirmation, .hold, .entitlement, .deadline]

def hasRole (r : Role) (t : TermRow) : Bool := t.role == some r

/-- The claims that mention a term whose role is `.stop`. -/
def stopBacking (b : BookView) : List ClaimRow :=
  let stops := (b.terms.filter (hasRole .stop)).map (·.id)
  b.claims.filter fun c => c.aboutIds.any stops.contains

def bookStopProblems (books : List BookView) (b : BookView) : List String :=
  let fix := "Declare the stop scene in the book: stopScene := .modelled, .waived \"<reason>\" or .inBook \"<title>\""
  match b.stopScene with
  | .undeclared => [s!"{b.title}: no stop scene is declared. {fix}"]
  | .modelled =>
    if !(b.terms.any (hasRole .stop)) then
      [s!"{b.title}: stopScene is .modelled, but no term has role := some .stop"]
    else
      let backing := stopBacking b
      let need (present : Bool) (what : String) : List String :=
        if present then [] else [s!"{b.title}: no claim about the stop term {what}"]
      need (backing.any (·.verdict == .counterexample)) "is a counterexample (a design that breaks)"
      ++ need (backing.any (·.verdict == .proved)) "is proved (a design that holds)"
      ++ need (backing.any (·.quint)) "has Quint evidence (the scene is not modelled)"
  | .waived reason =>
    let short := if !meaningful reason then
      [s!"{b.title}: stopScene is .waived without a reason of at least ten characters"] else []
    let inFlight := b.terms.filter fun t => inFlightRoles.any (hasRole · t)
    short ++ inFlight.map fun t =>
      s!"{b.title}: stopScene is .waived, but {t.label} has role {t.role.map shortName |>.getD ""}: something can be in flight across a stop, so model the scene"
  | .inBook title =>
    if title == b.title then [s!"{b.title}: stopScene is .inBook naming the book itself"] else
    match books.find? (·.title == title) with
    | none => [s!"{b.title}: stopScene is .inBook \"{title}\", but no registered book has that title"]
    | some other =>
      match other.stopScene with
      | .modelled => []
      | _ => [s!"{b.title}: stopScene is .inBook \"{title}\", but that book does not declare .modelled"]

/-- Every problem with the stop-scene declarations of the registered books. Empty means it holds. -/
def stopProblems (books : List BookView) : List String :=
  books.flatMap (bookStopProblems books)

def allRoles : List Role :=
  [.resource, .hold, .externalConfirmation, .entitlement, .stop, .plannedStop, .deadline,
   .fallbackChannel, .supplyCancellation, .reallocation]

/-- Keeps a text from closing the HTML comment it is printed in. -/
def commentSafe (s : String) : String := s.replace "-->" "- ->"

/-- The machine-readable line for `scripts/status.py` and the grader: ok or todo, then details. -/
def stopLine (books : List BookView) (b : BookView) : String :=
  match bookStopProblems books b, b.stopScene with
  | [], .modelled => "<!-- stop-scene: ok; modelled -->"
  | [], .waived reason => s!"<!-- stop-scene: ok; waived; {commentSafe reason} -->"
  | [], .inBook title => s!"<!-- stop-scene: ok; in book {commentSafe title} -->"
  | problems, _ => s!"<!-- stop-scene: todo; {commentSafe ("; ".intercalate problems)} -->"

def rolesDoc (l : Labels) (books : List BookView) : List String :=
  [l.header, "", s!"# {l.rolesTitle}", "", l.rolesIntro, ""] ++ books.flatMap fun b =>
    let tagged := allRoles.filter fun r => b.terms.any (hasRole r)
    let problems := bookStopProblems books b
    let declared := match b.stopScene with
      | .undeclared => l.stopUndeclared
      | .modelled => l.stopModelled
      | .waived reason => l.stopWaived ++ reason
      | .inBook title => l.stopInBook ++ title
    [s!"## {b.title}", "", stopLine books b, s!"<!-- roles-tagged: {tagged.length} -->", "",
     declared, ""]
    ++ (if problems.isEmpty then [] else [l.stopProblems, ""] ++ problems.map (s!"- {·}") ++ [""])
    ++ [l.roleColumns, separator l.roleColumns]
    ++ allRoles.map (fun r =>
      let names := (b.terms.filter (hasRole r)).map (·.label)
      s!"| {l.roleName r} | {if names.isEmpty then l.noTerm else ", ".intercalate names} |")
    ++ [""]
    ++ (match b.stopScene with
        | .modelled =>
          [s!"### {l.stopBackingTitle}", "", l.claimColumns, separator l.claimColumns]
          ++ (stopBacking b).map (fun c =>
            s!"| {l.verdict c.verdict} | {c.statement} | {c.about} | {c.evidence} |")
          ++ [""]
        | _ => [])

/-- Every generated document, the roles document included. -/
def allDocs (l : Labels) (books : List BookView) (control : Control) : List (String × List String) :=
  generatedDocs l books control ++ [("roles.md", rolesDoc l books)]

/-! ## Tests. They run on every `lake build`; a false one fails the build. -/

namespace StopSceneTest

def term (id : String) (role : Option Role := none) : TermRow :=
  { label := id, id, context := "", gloss := "", defDeps := "", assoc := "", anchors := [], role }

def claim (about : List String) (verdict : Verdict) (quint : Bool) : ClaimRow :=
  { verdict, statement := "", about := "", aboutIds := about, evidence := "", quint,
    witnessed := false, basisOk := true, industry := none }

def book (title : String) (terms : List TermRow) (claims : List ClaimRow) (scene : StopScene) :
    BookView :=
  { title, terms, claims, gate := [], stopScene := scene }

def ok (books : List BookView) : Bool := (stopProblems books).isEmpty

def stopTerms : List TermRow := [term "stop" (some .stop), term "payment" (some .externalConfirmation)]
def fullBacking : List ClaimRow :=
  [claim ["stop"] .counterexample true, claim ["stop", "payment"] .proved true]
def modelled : BookView := book "Cinema" stopTerms fullBacking .modelled

-- Nothing declared.
#guard !ok [book "B" stopTerms fullBacking .undeclared]
-- Modelled, with a counterexample, a proved result and Quint evidence about the stop term.
#guard ok [modelled]
-- A term merely named "stop" is not a stop: the role decides, not the word.
#guard !ok [book "B" [term "stop", term "emergencyStop"] fullBacking .modelled]
-- Only counterexamples about the stop term: no repaired design was shown to hold.
#guard !ok [book "B" stopTerms [claim ["stop"] .counterexample true] .modelled]
-- Only proved results: no design was shown to break.
#guard !ok [book "B" stopTerms [claim ["stop"] .proved true] .modelled]
-- A counterexample and a proof, both in Lean: the scene was never run as a model.
#guard !ok [book "B" stopTerms
  [claim ["stop"] .counterexample false, claim ["stop"] .proved false] .modelled]
-- Claims that do not mention the stop term do not back it.
#guard !ok [book "B" stopTerms
  [claim ["payment"] .counterexample true, claim ["payment"] .proved true] .modelled]
-- Waived, and nothing can be in flight.
#guard ok [book "Catalog" [term "product" (some .resource), term "stop" (some .stop)] []
  (.waived "the site only reads a nightly import and promises nothing outside")]
-- Waived, but an external confirmation exists.
#guard !ok [book "B" [term "payment" (some .externalConfirmation)] []
  (.waived "the site only reads a nightly import and promises nothing outside")]
-- Waived, but a deadline exists.
#guard !ok [book "B" [term "showtime" (some .deadline)] []
  (.waived "the site only reads a nightly import and promises nothing outside")]
-- Waived without a real reason.
#guard !ok [book "B" [] [] (.waived "n/a")]
-- Covered by another book that models the scene.
#guard ok [modelled, book "Orders" [] [] (.inBook "Cinema")]
-- Covered by a book that does not exist, by itself, or by a book that only waives.
#guard !ok [modelled, book "Orders" [] [] (.inBook "Missing")]
#guard !ok [modelled, book "Orders" [] [] (.inBook "Orders")]
#guard !ok [book "Catalog" [] [] (.waived "the site only reads a nightly import"),
  book "Orders" [] [] (.inBook "Catalog")]
-- The machine-readable line says ok only when there is no problem.
#guard stopLine [modelled] modelled == "<!-- stop-scene: ok; modelled -->"
#guard (stopLine [] (book "B" [] [] .undeclared)).startsWith "<!-- stop-scene: todo; "

end StopSceneTest

end Glossary
