# Seatbelt Lite

A Claude Code plugin that blocks three commands before they run:

- `rm -rf` on `/`, `~`, `$HOME` or the current folder
- `git push --force` (and `-f`, `--force-with-lease`)
- `git add -A` / `git add .` / `git add --all`

When it fires, Claude reads the reason and usually picks a safer way on the next try:

```
● Bash(git add -A && git commit -m "fix header spacing")
  ⎿ Seatbelt blocked this command: git add -A / git add . sweeps in
    .env files and other sessions' work. Add files by name.
● Bash(git add src/Header.tsx && git commit -m "fix header spacing")
  ⎿ [main 4e1c9a2] fix header spacing
```

`rm -rf node_modules`, `git push origin main` and `git add src/app.ts` still go through.

## Install

Inside Claude Code:

```
/plugin marketplace add OWNER/seatbelt-lite
/plugin install seatbelt-lite@seatbelt
```

Needs Python 3. No dependency, no network call.

## Why these three

I run Claude Code all day on live websites with permission prompts off. The `git add -A` one is real: another Claude session was working in the same folder and half of its unfinished changes ended up in my commit. A line in CLAUDE.md didn't stop it. A hook runs before the command, every time.

## Check it

```
python3 tests/run_tests.py
```

## The full version

[Seatbelt](https://seatbelt-hooks.achat-895.workers.dev) adds a longer shell list (`reset --hard`, `pkill -f`, `curl | sh`, `cat .env`, `supabase db reset --linked`...), a guard that refuses API keys in code, a SQL guard for Supabase RLS leaks through MCP, and a Stop hook that sends Claude back to check when it says "it's live" without verifying. 14 €, paid once.

## License

MIT
