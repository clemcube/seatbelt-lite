#!/usr/bin/env python3
# PreToolUse hook (Bash): blocks the three commands that cost the most when an agent runs them by mistake.
import json
import re
import sys

RULES = [
    (r"\brm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r|-r\s+-f|-f\s+-r)[a-z]*\s+(/|~|\$HOME|/\*|~/\*|\.\.?)(\s|/?$|;|&)",
     "rm -rf on /, ~, $HOME or the current folder. Delete the exact path you mean."),
    (r"\bgit\b[^;&|\n]*\bpush\b[^;&|\n]*(\s--force\b|\s-f\b|\s--force-with-lease\b)",
     "force push rewrites shared history. Push normally or ask the user."),
    (r"\bgit\b[^;&|\n]*\badd\b[^;&|\n]*(\s-A\b|\s--all\b|\s\.(\s|$))",
     "git add -A / git add . sweeps in .env files and other sessions' work. Add files by name."),
]


def check(command):
    for pattern, reason in RULES:
        if re.search(pattern, command, re.I):
            return reason
    return None


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0
    if event.get("tool_name") != "Bash":
        return 0
    reason = check((event.get("tool_input") or {}).get("command", ""))
    if reason:
        print(f"Seatbelt blocked this command: {reason}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
