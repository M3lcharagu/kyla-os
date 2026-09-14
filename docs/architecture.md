# KYLA Architecture

## Current architecture

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

## Planned architecture

```text
iPhone
   │
   ▼
WhatsApp
   │
   ▼
Webhook/API adapter
   │
   ▼
KYLA Router
   │
   ├── R1 HUMANITAS Command Center
   ├── R2 PATIENTIA Second Brain
   ├── ...
   └── R14 CASTITAS Life OS
          │
          ▼
       Agent adapter
          │
          ├── Claude
          ├── Codex
          ├── Copilot
          ├── Cursor
          ├── Docker Agent
          ├── Droid
          └── Shell
```

## Design rules

1. Keep the core router independent from WhatsApp.
2. Keep agent integrations replaceable.
3. Default to dry-run mode.
4. Never pass user input through a shell.
5. Allow Docker images explicitly instead of accepting arbitrary images.
6. Keep persistent memory out of the first version.
7. Add SQLite or a hosted database only after the command flow is stable.
8. Keep heavy models and long-running workloads outside the 8 GB laptop when possible.

## Command lifecycle

1. Receive a text command.
2. Select an explicit room if supplied.
3. Otherwise match room aliases.
4. Fall back to R1.
5. Select the room's default agent.
6. Apply dry-run protection.
7. Execute a configured local agent command, if available.
8. Return plain text suitable for CLI or WhatsApp.

## Suggested next additions

- A structured command format such as `/study`, `/research`, and `/dev`
- SQLite-based command history
- A WhatsApp webhook adapter
- Authentication and sender allow-listing
- Agent-specific adapters
- Docker job records and output limits
- A minimal Vercel dashboard
