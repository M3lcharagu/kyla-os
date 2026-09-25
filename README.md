# KYLA

KYLA is Mel's personal AI command center.

It is designed to be:

- Python-first
- Lightweight enough for an 8 GB RAM Windows 11 laptop
- CLI-first
- Compatible with Docker Sandboxes
- Ready for future WhatsApp integration
- Deployable later through Vercel Hobby
- Organized around 14 rooms and 7 possible agents

The current version is intentionally small. It routes commands locally but does not require
Claude, Codex, Docker, WhatsApp, or other external services to be installed.

## Rooms

| ID | Room | Purpose |
|---|---|---|
| R1 | HUMANITAS Command Center | Main command router |
| R2 | PATIENTIA Second Brain | Notes, memory, personal knowledge |
| R3 | TEMPERANTIA Trading Room | Trading research and journaling |
| R4 | INDUSTRIA Dev Lab | Software development |
| R5 | LUXURIA Creative Studio | Creative ideation and writing |
| R6 | GULA Editing Suite | Video and audio editing workflows |
| R7 | SUPERBIA Broadcast Room | Publishing and broadcasting |
| R8 | INVIDIA Photo Studio | Image and photography workflows |
| R9 | CARITAS Client Lounge | Client communication and delivery |
| R10 | HUMILITAS Study Room | School and learning |
| R11 | AVARITIA Business Ops | Business administration |
| R12 | ACEDIA Research | General research |
| R13 | IRA QA & Security | Testing and security |
| R14 | CASTITAS Life OS | Personal life management |

## Agents

- `claude`
- `codex`
- `copilot`
- `cursor`
- `docker-agent`
- `droid`
- `shell`
- `ollama` (local, wired — zero credits)
- `clip` / `capcut` (local CapCut-style shorts — zero credits)

Cloud agents stay `command: null` until you opt in. Local `ollama` and `clip` are wired in `config.yaml`.
Use `--execute` to override `runtime.dry_run: true`.

## Backend: Supabase (default, free tier)

KYLA's default backend for **database + logins** is [Supabase](https://supabase.com) (free tier).
It is default-on but lazy: with no keys set, the web UI stores history in `localStorage` and
Actions keep writing markdown files — nothing breaks before the project exists.

- **Web UI** (`web/supabase.js`): magic-link email login, signed-in state in the top bar,
  chats / tasks / agent runs sync to Supabase; `supabase-js` loads from a CDN only once
  configured (no build step).
- **Bridge + Actions** (`tools/supabase_sink.py`, stdlib only): write `agent_runs` and
  `news_briefs`; no-op when `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` are missing.
- **Schema + RLS**: [`supabase/migrations/0001_kyla_core.sql`](supabase/migrations/0001_kyla_core.sql)
  (profiles, agent_runs, chat_messages, tasks, memories, store_leads, news_briefs; owner-only policies).
- **Keep-alive**: `.github/workflows/supabase-keepalive.yml` pings twice a week.

Setup (3 values):

| Value | Goes to |
|---|---|
| Project URL | GitHub secret `SUPABASE_URL` **and** `web/config.js` → `KYLA_SUPABASE_URL` |
| anon / publishable key (public-safe) | `web/config.js` → `KYLA_SUPABASE_ANON_KEY` (or the UI account panel) |
| service_role / secret key (private) | GitHub secret `SUPABASE_SERVICE_ROLE_KEY` (+ `.env` on the bridge host) — never in `web/` |

**Free-tier limits (honest):** 50,000 monthly active users, 500 MB database, and
**free projects pause after about 1 week of inactivity** — the daily Actions writes plus the
keep-alive workflow keep it active; if it pauses, restore it from the dashboard.
Built-in auth email is limited to about 2 emails/hour.

Full steps: [`supabase/README.md`](supabase/README.md).

## Requirements

- Python 3.10+
- Optional: Docker Desktop
- Optional later: WhatsApp Business Cloud API credentials
- Optional: a free Supabase project (database + logins) — see `supabase/README.md`

## Local low-credit (recommended daily)

Prefer **Ollama** + the **clip** agent so daily use spends **$0** cloud credits.

```bash
bash scripts/setup_local.sh          # Linux / Mint / macOS
# .\scripts\setup_local.ps1         # Windows PowerShell
ollama pull qwen2.5:3b               # or phi4-mini
python main.py --agent ollama --execute "3 study tips"
python tools/clip_agent.py --help
```

Details: [`docs/LOCAL_LOW_CREDIT.md`](docs/LOCAL_LOW_CREDIT.md) · [`docs/CLIP_AGENT.md`](docs/CLIP_AGENT.md) · `make help`

## Setup on Windows 11

```powershell
cd kyla

py -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

## Setup on Linux / Linux Mint / macOS

```bash
cd kyla-os
bash scripts/setup_local.sh
source .venv/bin/activate
```

Or manually:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# optional video: pip install -r requirements-clip.txt
sudo apt install ffmpeg   # Debian / Mint
```

## Run KYLA

```powershell
python main.py "summarize my study plan"
```

KYLA will detect the most likely room from keywords.

Specify a room:

```powershell
python main.py --room R10 "explain recursion in Python"
```

Specify an agent:

```powershell
python main.py --room R4 --agent codex "create a Python CLI parser"
```

Preview routing without executing an agent:

```powershell
python main.py --dry-run "research beginner trading risk management"
```

Interactive mode:

```powershell
python main.py
```

Then type commands until entering:

```text
exit
```

## Configuring an agent

Open `config.yaml` and add a command.

Example:

```yaml
agents:
  shell:
    mode: local
    command: "python tools/shell_agent.py"
```

KYLA appends the user's prompt as the final argument:

```text
python tools/shell_agent.py "user prompt goes here"
```

Commands are executed without a shell, which avoids shell injection through user prompts.

## Docker

The Docker integration is disabled by default.

To allow a Docker image, add it to `runtime.allowed_docker_images` in `config.yaml`:

```yaml
runtime:
  allowed_docker_images:
    - "python:3.12-slim"
```

Then enable execution for a local test:

```powershell
$env:KYLA_ENABLE_DOCKER="1"
```

The Docker helper uses:

- No network
- Memory limits
- CPU limits
- A read-only container filesystem
- A temporary writable `/tmp`

Do not allow untrusted images.

## WhatsApp

`integrations/whatsapp_docker.py` contains a provider-neutral stub.

It currently accepts a WhatsApp-like payload and routes the message to KYLA.
Meta webhook verification, message sending, authentication, and persistence are intentionally
not implemented yet.

The recommended later flow is:

```text
WhatsApp
   ↓
small webhook service
   ↓
KYLA router
   ↓
room
   ↓
agent
   ↓
optional Docker sandbox
```

## Vercel

The current CLI is not a Vercel application.

When a web interface is needed, add a small API layer separately. Keep the command router
independent so it can be used by:

- The CLI
- A WhatsApp webhook
- A future Vercel API route
- An iPhone-friendly web interface

## Safety

This starter project does not automatically send WhatsApp messages, trade, publish content,
delete files, or run Docker containers unless explicitly configured.

Keep `runtime.dry_run: true` while building.
