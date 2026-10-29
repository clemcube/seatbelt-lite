# Seatbelt Lite

A Claude Code plugin for the two mistakes auto mode doesn't catch, plus three shell guards.

**"It's live" without checking.** A Stop hook reads the current turn. If a deploy ran (`vercel`, `wrangler deploy`, `netlify deploy`, `fly deploy`, `firebase deploy`) and the final message says "live" or "deployed" with no `curl`, `vercel inspect` or browser visit after it, Claude is sent back to check before it answers you.

**A Supabase view anon can read.** A PreToolUse hook reads the SQL Claude sends through MCP tools and refuses `create view public.…` without `security_invoker = true`. Without it, the view runs with its creator's rights, ignores RLS, and the anon key in your frontend can read it.

**Shell guards.** `rm -rf` on `/`, `~`, `$HOME` or the current folder, `git push --force`, and `git add -A` / `git add .`.

When a hook fires, Claude reads the reason and usually fixes its own approach on the next try:

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
/plugin marketplace add clemcube/seatbelt-lite
/plugin install seatbelt-lite@seatbelt
```

Needs Python 3. No dependency, no network call.

## Why

I run Claude Code all day on live websites. Each of these happened to me: a deploy announced as live that had failed at the build step, a view in `public` that anon could read until the Supabase advisor flagged it the next day, and another session's unfinished work swept into my commit by `git add -A`. The rules were in CLAUDE.md. A hook runs every time.

## Check it

```
python3 tests/run_tests.py
```

## The full version

[Seatbelt](https://seatbelt-hooks.achat-895.workers.dev/?ref=github) goes further: the SQL guard also covers `SECURITY DEFINER` functions open to anon, tables created without RLS, and `DELETE`/`UPDATE` without `WHERE`; the shell guard adds `reset --hard`, `pkill -f`, `curl | sh`, `cat .env`, `supabase db reset --linked` and more; a secret guard refuses API keys written into code. 14 €, paid once.

## License

MIT
