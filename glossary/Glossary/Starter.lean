import Glossary.Claim

/-!
# Starter glossary

A tiny glossary written only in the shared roles (resource, hold, external confirmation,
entitlement, emergency stop). It exists so that `just check` passes on a fresh project and shows
one claim of each kind. Write the glossary of your domain next to it and register that one in
`Glossary/Registry.lean`; until your book models its own stop scene, it points here with
`stopScene := .inBook "Starter"`. Once it declares the scene itself, delete this file,
`Spec/starter.qnt`, and their lines in `Glossary.lean`, `Glossary/Registry.lean`, `Audit.lean`, and
`Spec/tests.txt`.
-/

namespace Glossary.Starter

inductive Term where
  | customer | resource | hold | externalConfirmation | entitlement | emergencyStop
  deriving DecidableEq, Repr

inductive Ctx where
  | sales | external | operations
  deriving DecidableEq, Repr

open Term

def terms : List (Entry Term Ctx) := [
  { id := customer, label := "Customer", context := .sales,
    gloss := "A party that wants the resource", assoc := [hold] },
  { id := resource, label := "Resource", role := some .resource, context := .sales,
    gloss := "Something limited that cannot be given to two customers at once" },
  { id := hold, label := "Hold", role := some .hold, context := .sales,
    gloss := "A time-limited reservation of the resource for one customer",
    defDeps := [customer, resource] },
  { id := externalConfirmation, label := "External confirmation", role := some .externalConfirmation, context := .external,
    gloss := "A result produced outside the system; it cannot be stopped and may arrive late",
    defDeps := [customer] },
  { id := entitlement, label := "Entitlement", role := some .entitlement, context := .sales,
    gloss := "The hard-to-revoke right to the resource, issued to a customer",
    defDeps := [customer, resource, externalConfirmation] },
  { id := emergencyStop, label := "Emergency stop", role := some .stop, context := .operations,
    gloss := "The system autonomously stops accepting new holds and new confirmations",
    defDeps := [hold, externalConfirmation] }
]

theorem terms_wellFormed : WellFormed terms := check_sound _ (by decide)

def starter (main invariant : String) : QuintRef :=
  { file := "Spec/starter.qnt", main, invariant }

def claims : List (Claim Term) := [
  { about := [customer, resource, hold, entitlement],
    statement := "The glossary has unique IDs, no dangling references, and no circular definitions",
    verdict := .proved,
    evidence := .lean "Glossary.Starter.terms_wellFormed" (WellFormed terms) terms_wellFormed },
  { about := [entitlement, hold, externalConfirmation],
    statement := "In the naive design (issue on confirmation alone), at most one customer is entitled to the resource",
    verdict := .counterexample, evidence := .violated (starter "naive" "exclusive") },
  { about := [entitlement, hold, externalConfirmation, emergencyStop],
    statement := "In the guarded design (issue only while the hold is alive), at most one customer is entitled to the resource, even across an emergency stop",
    verdict := .proved, evidence := .holds (starter "guarded" "exclusive") },
  { about := [externalConfirmation, entitlement, emergencyStop],
    statement := "In the guarded design, no confirmed customer is left with neither an entitlement nor a refund",
    verdict := .counterexample, evidence := .violated (starter "guarded" "noOrphan") },
  { about := [externalConfirmation, entitlement, emergencyStop],
    statement := "How is a transaction resolved when its confirmation succeeds after the hold is gone?",
    verdict := .undecided, evidence := .question [starter "guarded" "noOrphan"] }
]

def book : Book Term Ctx := { title := "Starter", terms, claims, stopScene := .modelled }

theorem book_check : book.check = true := by decide

end Glossary.Starter
