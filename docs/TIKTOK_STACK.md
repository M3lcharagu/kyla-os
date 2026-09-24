# TikTok-sourced stack additions (always-wire, lazy-start)

Melvin’s six repos sit beside **Ruflo** (always-on orchestrator). Policy: **wired in REGISTRY/STACK**, lazy clone/pip, **no heavy clones** unless `KYLA_CLONE_HEAVY=1`. Catalina / 8GB safe.

| ID | Repo | Role | Install |
|---|---|---|---|
| `public-apis` | [public-apis/public-apis](https://github.com/public-apis/public-apis) | Free API catalog for agents | Shallow clone OK |
| `agent-reach` | [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach) | **ALWAYS** research/web read/search (~13+ platforms) | `pip install agent-reach && agent-reach install --env=auto --safe` |
| `awesome-llm-apps` | [Shubhamsaboo/awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) | 100+ agent/RAG templates (catalog) | Docs pointer; **do not** clone all by default |
| `openviking` | [volcengine/OpenViking](https://github.com/volcengine/OpenViking) | Browser/advanced agent | Lazy clone (heavy) |
| `awesome-harness-engineering` | [ai-boost/awesome-harness-engineering](https://github.com/ai-boost/awesome-harness-engineering) | Harness patterns for Ruflo | Docs / shallow OK |
| `anthropic-cybersecurity-skills` | [mukul975/Anthropic-Cybersecurity-Skills](https://github.com/mukul975/Anthropic-Cybersecurity-Skills) | Security skills pack | `npx skills add mukul975/Anthropic-Cybersecurity-Skills` |

## Rooms

- **R12 Research** — `agent-reach` LIVE + `public-apis` + Ruflo
- **R13 QA & Security** — cyber skills LIVE (no Docker required)
- **R1/R4** — Ruflo always-on; harness catalog on R1

## Mac / Catalina

```bash
cd ~/kyla-os && git pull origin main
source .venv/bin/activate
export KYLA_STACK_DIR="$HOME/kyla-stack" KYLA_CLONE_HEAVY=0
bash scripts/bootstrap_stack.sh
python tools/agent_reach_cli.py --ensure-only
python tools/integrations_cli.py list | grep -E 'agent-reach|public-apis|openviking|harness|cyber'
```

**Merge order:** land this stack PR first. `feat/online-ops` (Pages UI live replies / `online_bridge` / `web/app.js`) should merge **after** so Pages stay coordinated.
