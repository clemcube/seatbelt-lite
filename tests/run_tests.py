#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

GUARD = Path(__file__).resolve().parent.parent / "hooks" / "guard.py"

CASES = [
    ("rm -rf /", 2), ("rm -rf ~", 2), ("rm -fr .", 2), ("rm -rf $HOME", 2),
    ("git push --force origin main", 2), ("git push -f", 2),
    ("git add -A", 2), ("git add .", 2), ("git add --all && git commit -m x", 2),
    ("rm -rf node_modules", 0), ("rm -rf ./dist", 0), ("git push origin main", 0),
    ("git add src/app.ts", 0), ("git add .gitignore", 0), ("ls -la", 0),
]


def run(command):
    event = {"tool_name": "Bash", "tool_input": {"command": command}}
    return subprocess.run([sys.executable, str(GUARD)], input=json.dumps(event),
                          capture_output=True, text=True).returncode


failures = [(c, e, got) for c, e in CASES if (got := run(c)) != e]
for command, expected, got in failures:
    print(f"FAIL  {command!r}: expected {expected}, got {got}")
print(f"{len(CASES) - len(failures)}/{len(CASES)} passed")
sys.exit(1 if failures else 0)
