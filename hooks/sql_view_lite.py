#!/usr/bin/env python3
# PreToolUse hook (MCP tools): refuses a view in public without security_invoker, which anon can read past RLS.
import json
import re
import sys


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0
    sql = json.dumps(event.get("tool_input") or {})
    for stmt in re.findall(r"create\s+(?:or\s+replace\s+)?view\s+[^;]+", sql, re.I):
        if re.search(r"\bpublic\.", stmt, re.I) and "security_invoker" not in stmt.lower():
            print("Seatbelt blocked this SQL: a view in public runs with its creator's rights, ignores RLS, "
                  "and anon can read it. Add with (security_invoker = true).", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
