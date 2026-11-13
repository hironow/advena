/-!
# Progress

If every unresolved state has a step that strictly decreases a measure, a resolved state is
reachable from every state. Conversely, an unresolved state with no step never reaches one.
This holds for any state type and any step relation, so every domain can use it.
-/

namespace Glossary.Progress

/-- Reachable in zero or more steps. -/
inductive Reach {S : Type} (step : S → S → Prop) : S → S → Prop where
  | refl (s : S) : Reach step s s
  | next {s t u : S} : step s t → Reach step t u → Reach step s u

theorem resolvable_within {S : Type} (step : S → S → Prop) (resolved : S → Prop) (μ : S → Nat)
    (progress : ∀ s, ¬ resolved s → ∃ t, step s t ∧ μ t < μ s) :
    ∀ n s, μ s ≤ n → ∃ t, Reach step s t ∧ resolved t := by
  intro n
  induction n with
  | zero =>
    intro s h
    apply Classical.byContradiction
    intro hno
    have hr : ¬ resolved s := fun hr => hno ⟨s, .refl s, hr⟩
    obtain ⟨t, _, hlt⟩ := progress s hr
    omega
  | succ n ih =>
    intro s h
    apply Classical.byContradiction
    intro hno
    have hr : ¬ resolved s := fun hr => hno ⟨s, .refl s, hr⟩
    obtain ⟨t, hst, hlt⟩ := progress s hr
    obtain ⟨u, htu, hu⟩ := ih t (by omega)
    exact hno ⟨u, .next hst htu, hu⟩

/-- With progress, a resolved state is reachable from every state. -/
theorem resolvable {S : Type} (step : S → S → Prop) (resolved : S → Prop) (μ : S → Nat)
    (progress : ∀ s, ¬ resolved s → ∃ t, step s t ∧ μ t < μ s) :
    ∀ s, ∃ t, Reach step s t ∧ resolved t :=
  fun s => resolvable_within step resolved μ progress (μ s) s (Nat.le_refl _)

/-- An unresolved state with no step never reaches a resolved state. -/
theorem stuck_never_resolves {S : Type} (step : S → S → Prop) (resolved : S → Prop) (s : S)
    (unresolved : ¬ resolved s) (stuck : ∀ t, ¬ step s t) :
    ∀ t, Reach step s t → ¬ resolved t := by
  intro t h
  cases h with
  | refl => exact unresolved
  | next hst _ => exact absurd hst (stuck _)

end Glossary.Progress
