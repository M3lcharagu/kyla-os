# KYLA Architecture

## Current architecture (CLI core)

```text
CLI
 │
 ▼
main.py
 │
 ├── room selection
 ├── agent selection
 ├── dry-run protection
 └── optional local subprocess
```

## Jarvis stack (HeyClicky + Kyla + Quant Mind)

See **`docs/JARVIS_HEYCLICKY_KYLA.md`** for the full fusion blueprint.

```text
HeyClicky (interface)
   │  voice · screen · point · type
   ▼
Jarvis orchestrator
   │
   ├── Kyla (health / longevity specialist)
   ├── Quant Mind (paper markets specialist)
   ├── ruflo / stack / ollama (general)
   └── Memory (profile, journal, goals)
          │
          ▼
       Execution (local agents, APIs, paper only)
```

| Layer | Implementation |
|-------|----------------|
| Interface | `agents.heyclicky` → `tools/heyclicky_bridge.py` |
| Orchestrator | `agents.jarvis` → `tools/jarvis_orchestrator.py` |
| Health specialist | `agents.kyla-health` → `tools/kyla_health_agent.py` · room R15 |
| Quant specialist | `agents.quant-mind` → `tools/quant_mind_agent.py` · room R3 |
| Memory | `memory/` (local; example profile only in git) |

## Planned external path

```text
iPhone / desktop
   │
   ▼
WhatsApp / HeyClicky UI
   │
   ▼
Webhook / local bridge (auth + allowlist)
   │
   ▼
KYLA Router (main.py / jarvis_orchestrator)
   │
   ├── R1–R14 existing rooms
   ├── R15 Kyla Health
   └── Specialists + memory
```

## Design rules

1. Keep the core router independent from WhatsApp and HeyClicky transport.
2. Keep agent integrations replaceable.
3. Default to dry-run mode.
4. Never pass user input through a shell.
5. Allow Docker images explicitly instead of accepting arbitrary images.
6. Health and market outputs fail closed: educational / paper framing only.
7. Add SQLite only after command flow and memory policy are stable.
8. Keep heavy models outside the 8 GB laptop when possible; prefer Ollama small models.
9. R13 QA/security/legal gate remains mandatory before any external side effect.

## Command lifecycle

1. Receive a text (or future voice/screen) command.
2. Select explicit room if supplied.
3. Otherwise match room aliases (including health / quant keywords).
4. Fall back to R1 or jarvis orchestrator when using `--agent jarvis`.
5. Select the room's default agent or explicit specialist.
6. Apply dry-run protection.
7. Execute a configured local agent command, if available.
8. Return plain text suitable for CLI, WhatsApp, or HeyClicky TTS.

## Suggested next additions

- Structured command format (`/health`, `/quant`, `/study`)
- SQLite command history + encrypted health profile option
- HeyClicky native IPC
- WhatsApp webhook adapter with sender allowlist
- Agent-specific adapters
- Docker job records and output limits (Linux Mint native Engine only)
- Minimal static dashboard already under `dashboard/`
