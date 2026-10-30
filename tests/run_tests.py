#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent / "hooks"

BASH = [
    ("rm -rf /", 2), ("rm -rf ~", 2), ("rm -fr .", 2), ("rm -rf $HOME", 2),
    ("git push --force origin main", 2), ("git push -f", 2),
    ("git add -A", 2), ("git add .", 2), ("git add --all && git commit -m x", 2),
    ("rm -rf node_modules", 0), ("rm -rf ./dist", 0), ("git push origin main", 0),
    ("git add src/app.ts", 0), ("git add .gitignore", 0), ("ls -la", 0),
]

SQL = [
    ("create view public.v as select 1", 2),
    ("CREATE OR REPLACE VIEW public.quotes AS select * from q", 2),
    ("create view public.v with (security_invoker = true) as select 1", 0),
    ("create view private.v as select 1", 0),
    ("select * from public.v", 0),
]


def user(text):
    return {"type": "user", "message": {"role": "user", "content": text}}


def tool(command, name="Bash"):
    return {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "tool_use", "name": name, "input": {"command": command}}]}}


def result():
    return {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "content": "ok"}]}}


def say(text):
    return {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}


DEPLOY = [tool("npx wrangler deploy"), result()]
CURL = [tool("curl -sI https://example.com"), result()]

STOP = [
    ("deploy then claim, no check", [user("ship it")] + DEPLOY + [say("Deployed, it's live.")], True),
    ("deploy, curl, claim", [user("ship it")] + DEPLOY + CURL + [say("It's live, HTTP 200.")], False),
    ("curl before deploy only", [user("ship it")] + CURL + DEPLOY + [say("It's live.")], True),
    ("vercel prod no check", [user("go"), tool("vercel --prod"), result(), say("Now live on prod.")], True),
    ("browser check counts", [user("go")] + DEPLOY + [tool("x", "mcp__claude-in-chrome__navigate"), result(),
                                                       say("It's live.")], False),
    ("negation", [user("go")] + DEPLOY + [say("The build failed, so it is not deployed.")], False),
    ("claim with a question after", [user("go")] + DEPLOY + [say("Deployed, it's live. Want me to tag it?")], True),
    ("no deploy this turn", [user("old")] + DEPLOY + [say("done")] + [user("explain")] +
     [say("It's live since yesterday.")], False),
    ("no claim", [user("go")] + DEPLOY + [say("Deploy command finished, checking next.")], False),
    ("vercel inspect is the check", [user("go"), tool("vercel --prod"), result(), tool("vercel inspect https://a.vercel.app"),
                                     result(), say("It's live.")], False),
    ("reading vercel.json is no deploy", [user("go"), tool("cat vercel.json"), result(), say("It's deployed on Vercel.")], False),
    ("vercel logs is no deploy", [user("go"), tool("vercel logs https://a.vercel.app"), result(), say("It's live.")], False),
    ("curl chained after deploy", [user("go"), tool("vercel --prod && curl -sI https://a.com"), result(), say("It's live.")], False),
    ("curl chained before deploy", [user("go"), tool("curl -sI https://a.com && vercel --prod"), result(), say("It's live.")], True),
    ("npx vercel deploy", [user("go"), tool("npx vercel deploy --prod"), result(), say("It's live.")], True),
    ("bare vercel", [user("go"), tool("vercel"), result(), say("It's live.")], True),
    ("curl on localhost is no proof", [user("go")] + DEPLOY + [tool("curl -sI http://localhost:3000"), result(), say("It's live.")], True),
]


def run(hook, event):
    return subprocess.run([sys.executable, str(HOOKS / hook)], input=json.dumps(event),
                          capture_output=True, text=True)


def stop_blocks(entries, active=False):
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
        f.write("\n".join(json.dumps(e) for e in entries))
    out = run("proof_lite.py", {"transcript_path": f.name, "stop_hook_active": active}).stdout
    Path(f.name).unlink()
    return '"block"' in out


failures = []
for command, expected in BASH:
    got = run("guard.py", {"tool_name": "Bash", "tool_input": {"command": command}}).returncode
    if got != expected:
        failures.append(f"bash {command!r}: expected {expected}, got {got}")
for sql, expected in SQL:
    got = run("sql_view_lite.py", {"tool_name": "mcp__supabase__execute_sql", "tool_input": {"query": sql}}).returncode
    if got != expected:
        failures.append(f"sql {sql!r}: expected {expected}, got {got}")
for label, entries, expected in STOP:
    if stop_blocks(entries) != expected:
        failures.append(f"stop {label}: expected block={expected}")
if stop_blocks(STOP[0][1], active=True):
    failures.append("stop: must not block when stop_hook_active")
if run("proof_lite.py", {"transcript_path": "/nonexistent"}).stdout:
    failures.append("stop: must fail open on a missing transcript")

total = len(BASH) + len(SQL) + len(STOP) + 2
for f in failures:
    print("FAIL ", f)
print(f"{total - len(failures)}/{total} passed")
sys.exit(1 if failures else 0)
