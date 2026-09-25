# Ruflo Health — 2026-09-25T12:06:30Z

## Policy
- KYLA runtime.default_agent must be **ruflo** (always-on).
- This job never sets Anthropic/OpenAI keys.

## node / npx
```
v20.20.2
10.8.2
```

## npx ruflo@latest --version
```
ruflo v3.45.0
```

## KYLA dry-run routes to ruflo
```
[KYLA] R1 · HUMANITAS Command Center
[AGENT] ruflo (local)
[PROMPT] plan my week in humanitas
[SUITE] command
[ORCHESTRATOR] ruflo always-on — python tools/ruflo_agent.py
[STACK] ruflo · Ruflo (agent meta-harness) (wired, orchestrator — uses Claude/Codex when present; prefer Ollama/local bridge ($0), R1,R4,R2,R5,R10,R12,R11,R13)
  https://github.com/ruvnet/ruflo
  python tools/integrations_cli.py run ruflo
[STATUS] Dry run; nothing executed.
[KYLA] R6 · GULA Editing Suite
[AGENT] clip (local)
[PROMPT] clip a youtube short in gula
[SUITE] video
[STACK] clip · KYLA clip agent (CapCut-style) (wired, local/$0, R6,R7)
  https://github.com/M3lcharagu/kyla-clip
  python tools/integrations_cli.py run clip
[STATUS] Dry run; nothing executed.
```

## 24/7 notes
- Scheduled Actions need zero Melvin. Interactive bots need online_bridge host.
- See docs/ONLINE.md.
