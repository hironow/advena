import Glossary

/-! Prints the axioms the proofs use. `just lean-check` rejects `sorryAx` and friends.
Add one line for every theorem that a claim cites as evidence. -/

#print axioms Glossary.check_sound
#print axioms Glossary.check_add
#print axioms Glossary.Progress.resolvable
#print axioms Glossary.Starter.terms_wellFormed
#print axioms Glossary.Starter.book_check
