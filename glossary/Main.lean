import Glossary.Registry
import Glossary.StopScene
import Glossary.Questions
import Glossary.Control

/-!
Prints the list of checks and writes the generated documents.
  claims gate        the Quint checks, tab-separated: expectation, kind, file, module, property
  claims docs <dir>  write the generated documents into <dir>
  claims anchors     the code anchors, tab-separated: term ID, anchor
  claims terms       every term ID, one per line
  claims stop        check the stop-scene declarations; exit 1 and list the problems if any
  claims questions   check that every question states its basis; exit 1 and list the problems if any
  claims control     print the control declaration (run, skipped, undeclared); exit 1 if it is malformed

This file is the same for every domain. Register glossaries in `Glossary/Registry.lean`.
-/

open Glossary

def main (args : List String) : IO UInt32 := do
  match args with
  | ["gate"] =>
    for l in books.flatMap (·.gate) do
      IO.println l
    return 0
  | ["docs", dir] =>
    IO.FS.createDirAll dir
    let docs := allDocs labels books control
    -- Drop files that are no longer generated, so the folder holds exactly the current output.
    for entry in (← System.FilePath.readDir dir) do
      if !(docs.any (·.1 == entry.fileName)) && !(← entry.path.isDir) then
        IO.FS.removeFile entry.path
    for (name, lines) in docs do
      IO.FS.writeFile (System.FilePath.mk dir / name) ("\n".intercalate lines ++ "\n")
    return 0
  | ["anchors"] =>
    for l in anchorLines books do
      IO.println l
    return 0
  | ["stop"] =>
    let problems := stopProblems books
    for p in problems do
      IO.eprintln s!"stop-check: {p}"
    if problems.isEmpty then
      IO.println s!"stop-check: {books.length} glossaries declare their stop scene, and the declarations hold"
      return 0
    else
      return 1
  | ["questions"] =>
    let problems := questionProblems books
    for p in problems do
      IO.eprintln s!"question-check: {p}"
    if problems.isEmpty then
      IO.println "question-check: every question rests on counterexamples or says why no model shows it"
      return 0
    else
      return 1
  | ["control"] =>
    let problems := controlProblems control
    for p in problems do
      IO.eprintln s!"control-check: {p}"
    if problems.isEmpty then
      IO.println (controlWord control)
      return 0
    else
      return 1
  | ["terms"] =>
    for l in termIds books do
      IO.println l
    return 0
  | _ =>
    IO.eprintln "usage: claims (gate | docs <dir> | anchors | terms | stop | questions | control)"
    return 2
