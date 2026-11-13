import Glossary

/-! Prints the axioms the proofs use. `just lean-check` rejects `sorryAx` and friends.
Add one line for every theorem that a claim cites as evidence. -/

#print axioms Glossary.check_sound
#print axioms Glossary.check_add
#print axioms Glossary.Progress.resolvable
#print axioms Glossary.Advena.terms_wellFormed
#print axioms Glossary.Advena.book_check
#print axioms Glossary.Advena.creating_is_overloaded
#print axioms Glossary.Advena.day_depends_on_production_time
