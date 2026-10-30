#!/usr/bin/env python3
# Stop hook: if this turn ran a deploy and the answer says "live" without checking afterwards, send Claude back.
import json
import re
import sys

DEPLOY = re.compile(
    r"^\s*(\w+=\S*\s+)*(npx\s+(-y\s+)?)?"
    r"(vercel(@\S+)?(\s+(deploy|promote|--prod|--yes|-y|--prebuilt)\b|\s*$)"
    r"|wrangler(@\S+)?\s+(pages\s+)?deploy\b|netlify\s+deploy\b|fly\s+deploy\b|firebase\s+deploy\b)", re.I)
CHECK = re.compile(r"\b(curl|wget|vercel\s+inspect)\b|navigate|WebFetch", re.I)
LOCAL = re.compile(r"\b(localhost|127\.0\.0\.1|0\.0\.0\.0)\b|\[::1\]", re.I)
CLAIM = re.compile(r"\b(it'?s live|is live|now live|deployed)\b", re.I)
NEGATION = re.compile(r"(\bnot|n't|\bnever)\b[^.\n]{0,20}\b(live|deployed)\b", re.I)


def is_user_prompt(entry):
    if entry.get("type") != "user":
        return False
    content = (entry.get("message") or {}).get("content")
    return isinstance(content, str) or any(
        isinstance(b, dict) and b.get("type") == "text" for b in content or [])


def current_turn(path):
    entries = [json.loads(line) for line in open(path) if line.strip()]
    start = max((i for i, e in enumerate(entries) if is_user_prompt(e)), default=-1)
    return entries[start + 1:]


def steps(block):
    if block.get("name") == "Bash":
        return re.split(r"&&|\|\||[;|\n]", (block.get("input") or {}).get("command", ""))
    return [block.get("name", "")]


def main():
    try:
        event = json.load(sys.stdin)
        if event.get("stop_hook_active"):
            return 0
        actions, last_text = [], ""
        for entry in current_turn(event["transcript_path"]):
            for block in (entry.get("message") or {}).get("content") or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    actions.extend(steps(block))
                elif block.get("type") == "text":
                    last_text = block.get("text", "")
    except Exception:
        return 0
    deploys = [i for i, a in enumerate(actions) if DEPLOY.search(a)]
    if not deploys or not CLAIM.search(last_text) or NEGATION.search(last_text):
        return 0
    if any(CHECK.search(a) and not LOCAL.search(a) for a in actions[deploys[-1] + 1:]):
        return 0
    print(json.dumps({"decision": "block", "reason":
        "Seatbelt: you said it is deployed or live, but nothing checked the result after the last deploy. "
        "Fetch the URL (curl -sI, then a piece of the new content) or read the deployment status, then answer."}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
