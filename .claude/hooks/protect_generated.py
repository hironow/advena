"""Stop edits to the generated documents (docs/generated/). A Claude Code PreToolUse hook.

Only `just generate` writes the generated documents. This hook refuses Edit / Write calls on them
and shell commands that rewrite them. Exit code 2 stops the tool call and returns the message to Claude.
The real guarantee is `just generated-check`; this hook only stops the mistake earlier.
"""

import json
import re
import sys

GENERATED = "docs/generated"
# A redirect counts only when its target is the generated directory. The other commands count
# when the directory appears among their arguments.
WRITE_TO_GENERATED = re.compile(
    r">>?\s*[\"']?[^\s\"'|;&]*"
    + GENERATED
    + r"|(?:^|[|;&]\s*|\bxargs\s+)(?:tee|sed\s+-i|rm|mv|cp|truncate|chmod)\b[^|;&\n]*"
    + GENERATED,
    re.MULTILINE,
)
MESSAGE = (
    f"{GENERATED}/ holds generated documents and is never edited by hand. "
    "To change their content, edit Glossary/*.lean and run `just generate`."
)


def main():
    call = json.load(sys.stdin)
    tool = call.get("tool_name", "")
    args = call.get("tool_input", {})
    if tool in ("Edit", "Write", "NotebookEdit"):
        path = str(args.get("file_path") or args.get("notebook_path") or "")
        if f"/{GENERATED}/" in path or path.startswith(f"{GENERATED}/"):
            print(MESSAGE, file=sys.stderr)
            return 2
    if tool == "Bash" and WRITE_TO_GENERATED.search(str(args.get("command", ""))):
        print(MESSAGE, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
