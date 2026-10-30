#!/usr/bin/env python3
# PreToolUse hook (MCP tools): refuses a view in public without security_invoker, which anon can read past RLS.
import json
import re
import sys

VIEW = re.compile(r"create\s+(?:or\s+replace\s+)?(materialized\s+)?view\s+(?:if\s+not\s+exists\s+)?([\w.\"]+)([^;]*)", re.I)
INVOKER = re.compile(r"\bsecurity_invoker\b(\s*=\s*(on|true|1|yes)\b|\s*[,)])", re.I)


def in_public(name):
    parts = name.replace('"', "").lower().split(".")
    return len(parts) == 1 or parts[0] == "public"


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0
    sql = " ".join(v for v in (event.get("tool_input") or {}).values() if isinstance(v, str))
    for materialized, name, rest in VIEW.findall(sql):
        if in_public(name) and (materialized or not INVOKER.search(rest)):
            print("Seatbelt blocked this SQL: a view in public runs with its creator's rights, ignores RLS, "
                  "and anon can read it. Add with (security_invoker = true), or put it in a private schema.", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
