/-!
# Provable glossary: the foundation

A glossary is a list of entries. A broken glossary (duplicate IDs, dangling references,
circular definitions) can be written down as it is. If the checker `check` returns `true`,
the glossary is `WellFormed` (`check_sound`). The theorem holds for every glossary.

This file is the same for every domain. Do not edit it per project.
-/

namespace Glossary

/-- The shared roles a term can play in its domain (SKILL.md, "Map the domain onto shared roles").
`docs/generated/roles.md` lists them from the glossary, and the stop-scene rule
(`Glossary/StopScene.lean`) reads them. -/
inductive Role where
  | resource | hold | externalConfirmation | entitlement | stop | plannedStop | deadline
  | fallbackChannel | supplyCancellation | reallocation
  deriving DecidableEq, Repr

/-- One glossary entry. `ι` is the term ID type, `κ` the bounded context type. -/
structure Entry (ι κ : Type) where
  id : ι
  /-- Human-readable name. -/
  label : String := ""
  context : κ
  /-- Natural-language definition. The machine does not read its meaning. -/
  gloss : String
  /-- Definitional dependencies: terms needed to understand this definition. Cycles are forbidden. -/
  defDeps : List ι := []
  /-- Domain associations, such as "a customer places orders". Cycles are allowed. -/
  assoc : List ι := []
  /-- Code anchors: where the implementation realises this term, each written `path#text`
  (path from the repository root, then a piece of text that must occur in that file).
  `just check` fails when the file is gone or no longer contains the text, so a rename in the
  code cannot silently detach the glossary from it. Leave empty when there is no implementation.

  An anchor that starts with `!` asserts absence: `!path#text` passes while the file does not
  contain the text. Use it for a definition that rests on something the code does not do
  ("nothing ever sets this status"), so that the gate fails the day someone adds it. -/
  anchors : List String := []
  /-- The shared role this term plays, if any. Tag every term that plays one: the role table is
  generated from these tags, and an untagged role is reported as absent. -/
  role : Option Role := none

variable {ι κ : Type}

def ids (g : List (Entry ι κ)) : List ι := g.map (·.id)

/-- The definition of `a` depends on `b`. -/
def DefDep (g : List (Entry ι κ)) (a b : ι) : Prop :=
  ∃ e, e ∈ g ∧ e.id = a ∧ b ∈ e.defDeps

/-- No path of one or more steps leads back to its start. -/
def Acyclic {α : Type} (r : α → α → Prop) : Prop :=
  ∀ t, ¬ Relation.TransGen r t t

/-- Formal well-formedness of a glossary. It says nothing about whether the meaning is right. -/
structure WellFormed (g : List (Entry ι κ)) : Prop where
  uniqueIds : (ids g).Nodup
  defRefsExist : ∀ e, e ∈ g → ∀ d, d ∈ e.defDeps → d ∈ ids g
  assocRefsExist : ∀ e, e ∈ g → ∀ d, d ∈ e.assoc → d ∈ ids g
  acyclic : Acyclic (DefDep g)

/-- A relation is acyclic if some function strictly decreases along every edge. -/
theorem acyclic_of_rank {α : Type} {r : α → α → Prop} (f : α → Nat)
    (h : ∀ a b, r a b → f b < f a) : Acyclic r := by
  intro t ht
  have key : ∀ a b, Relation.TransGen r a b → f b < f a := by
    intro a b hab
    induction hab with
    | single h1 => exact h _ _ h1
    | tail _ h2 ih => exact Nat.lt_trans (h _ _ h2) ih
  exact Nat.lt_irrefl _ (key t t ht)

theorem defDep_reverse (g : List (Entry ι κ)) (a b : ι) :
    DefDep g.reverse a b ↔ DefDep g a b := by
  simp [DefDep]

theorem transGen_mono {α : Type} {r s : α → α → Prop} (h : ∀ a b, r a b → s a b)
    {a b : α} (hab : Relation.TransGen r a b) : Relation.TransGen s a b := by
  induction hab with
  | single h1 => exact .single (h _ _ h1)
  | tail _ h2 ih => exact .tail ih (h _ _ h2)

variable [DecidableEq ι]

/-- Definitional dependencies that cross bounded contexts, as (dependent, depended-on) pairs. -/
def contextEdges [DecidableEq κ] (g : List (Entry ι κ)) : List (κ × κ) :=
  g.flatMap fun e =>
    (g.filter fun d => decide (d.id ∈ e.defDeps) && decide (d.context ≠ e.context)).map
      fun d => (e.context, d.context)

/-- Check a list whose newest entry comes first.
Each ID is new, and each definitional dependency points to an older entry (define before use). -/
def checkNewestFirst : List (Entry ι κ) → Bool
  | [] => true
  | e :: older =>
    decide (e.id ∉ ids older)
      && e.defDeps.all (fun d => decide (d ∈ ids older))
      && checkNewestFirst older

def assocResolved (g : List (Entry ι κ)) : Bool :=
  g.all fun e => e.assoc.all fun d => decide (d ∈ ids g)

/-- The glossary checker. Entries are listed in the order they were written (oldest first). -/
def check (g : List (Entry ι κ)) : Bool :=
  checkNewestFirst g.reverse && assocResolved g

/-- Rank: the number of older entries plus one, or 0 if the term is absent. -/
def rank : List (Entry ι κ) → ι → Nat
  | [], _ => 0
  | e :: older, a => if e.id = a then older.length + 1 else rank older a

theorem rank_le (g : List (Entry ι κ)) (a : ι) : rank g a ≤ g.length := by
  induction g with
  | nil => simp [rank]
  | cons e older ih =>
    simp only [rank, List.length_cons]
    split
    · exact Nat.le_refl _
    · exact Nat.le_succ_of_le ih

theorem nodup_of_check : ∀ (g : List (Entry ι κ)), checkNewestFirst g = true → (ids g).Nodup
  | [], _ => by simp [ids]
  | e :: older, h => by
    simp only [checkNewestFirst, Bool.and_eq_true, decide_eq_true_eq] at h
    have ih := nodup_of_check older h.2
    simp only [ids, List.map_cons, List.nodup_cons]
    exact ⟨h.1.1, ih⟩

/-- If the check passes, every dependency target exists and has a strictly smaller rank. -/
theorem step_of_check : ∀ (g : List (Entry ι κ)), checkNewestFirst g = true →
    ∀ a b, DefDep g a b → b ∈ ids g ∧ rank g b < rank g a
  | [], _, a, b, ⟨e, he, _⟩ => by simp at he
  | e :: older, h, a, b, ⟨e', he', hid, hb⟩ => by
    simp only [checkNewestFirst, Bool.and_eq_true, decide_eq_true_eq, List.all_eq_true] at h
    obtain ⟨⟨hfresh, hdeps⟩, hrest⟩ := h
    have inOlder : b ∈ ids older := by
      rcases List.mem_cons.mp he' with rfl | hmem
      · exact hdeps b hb
      · exact (step_of_check older hrest a b ⟨e', hmem, hid, hb⟩).1
    have hbne : e.id ≠ b := fun hEq => hfresh (hEq ▸ inOlder)
    refine ⟨by simp only [ids, List.map_cons, List.mem_cons]; exact Or.inr inOlder, ?_⟩
    have rb : rank (e :: older) b = rank older b := by simp [rank, hbne]
    rw [rb]
    rcases List.mem_cons.mp he' with rfl | hmem
    · subst hid
      have ra : rank (e' :: older) e'.id = older.length + 1 := by simp [rank]
      rw [ra]
      exact Nat.lt_succ_of_le (rank_le older b)
    · have hane : e.id ≠ a := by
        intro hEq
        apply hfresh
        rw [hEq, ← hid]
        exact List.mem_map_of_mem hmem
      have ra : rank (e :: older) a = rank older a := by simp [rank, hane]
      rw [ra]
      exact (step_of_check older hrest a b ⟨e', hmem, hid, hb⟩).2

/-- **Soundness**: if `check` passes, the glossary is well-formed. Holds for every glossary. -/
theorem check_sound (g : List (Entry ι κ)) (h : check g = true) : WellFormed g := by
  simp only [check, Bool.and_eq_true] at h
  obtain ⟨hord, hassoc⟩ := h
  have hstep := step_of_check g.reverse hord
  have hids : ∀ x, x ∈ ids g.reverse ↔ x ∈ ids g := by intro x; simp [ids]
  refine ⟨?_, ?_, ?_, ?_⟩
  · have h1 := nodup_of_check g.reverse hord
    have h2 : (ids g).reverse.Nodup := by simpa [ids, List.map_reverse] using h1
    unfold List.Nodup at h2 ⊢
    exact (List.pairwise_reverse.mp h2).imp (fun hne => Ne.symm hne)
  · intro e he d hd
    exact (hids d).mp (hstep e.id d ⟨e, by simpa using he, rfl, hd⟩).1
  · intro e he d hd
    simp only [assocResolved, List.all_eq_true, decide_eq_true_eq] at hassoc
    exact hassoc e he d hd
  · have : Acyclic (DefDep g.reverse) :=
      acyclic_of_rank (rank g.reverse) (fun a b hab => (hstep a b hab).2)
    intro t ht
    apply this t
    exact transGen_mono (fun a b hab => (defDep_reverse g a b).mpr hab) ht

/-- **Preservation under extension**: adding a term defined only from existing terms keeps the
check passing. No number of such additions creates a cycle. -/
theorem check_add (g : List (Entry ι κ)) (e : Entry ι κ) (h : check g = true)
    (fresh : e.id ∉ ids g)
    (defs : ∀ d, d ∈ e.defDeps → d ∈ ids g)
    (assocs : ∀ d, d ∈ e.assoc → d ∈ ids g ∨ d = e.id) :
    check (g ++ [e]) = true := by
  simp only [check, Bool.and_eq_true] at h ⊢
  obtain ⟨hord, hassoc⟩ := h
  have hids : ∀ x, x ∈ ids g.reverse ↔ x ∈ ids g := by intro x; simp [ids]
  constructor
  · simp only [List.reverse_append, List.reverse_cons, List.reverse_nil, List.nil_append,
      List.singleton_append, checkNewestFirst, Bool.and_eq_true, decide_eq_true_eq,
      List.all_eq_true]
    exact ⟨⟨fun hin => fresh ((hids _).mp hin), fun d hd => (hids d).mpr (defs d hd)⟩, hord⟩
  · simp only [assocResolved, List.all_eq_true, decide_eq_true_eq] at hassoc ⊢
    intro e' he' d hd
    simp only [ids, List.map_append, List.map_cons, List.map_nil, List.mem_append,
      List.mem_singleton]
    rcases List.mem_append.mp he' with hmem | hlast
    · exact Or.inl (hassoc e' hmem d hd)
    · have : e' = e := by simpa using hlast
      subst this
      exact assocs d hd

end Glossary
