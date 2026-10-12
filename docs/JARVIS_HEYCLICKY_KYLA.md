# HeyClicky ↔ Kyla ↔ Quant Mind → Jarvis

**Status:** Scaffold integrated into kyla-os (2026-10-12). Interface and specialist stubs are wired; full computer-use / screen capture / live medical APIs remain gated behind R13 and explicit opt-in.

> **Boundaries:** Not medical advice. Not financial advice. No live trading. No autonomous diagnosis. Paper / research / education only until R13 + human approval.

## 1. Core link: HeyClicky ↔ Kyla

| Role | Component | Responsibility |
|------|-----------|----------------|
| **Interface** | HeyClicky ("helloclicky") | Always-present, screen-aware, voice-first cursor buddy: sees what you see, talks, points, types, spawns agents |
| **Health specialist** | Kyla | Deep domain expert for biomarkers, risk prediction, longevity protocols, lab interpretation, personalized action *plans* (research framing) |
| **Finance specialist** | Quant Mind (kyla-quant) | Paper research, signals, risk, journal — never live execution in this scaffold |
| **Orchestrator** | Jarvis brain (`tools/jarvis_orchestrator.py`) | Routes intent → specialist → memory → response |

### Natural fusion

1. **HeyClicky** is the front door and continuous observer for everything — including health context.
2. **Kyla** is the domain expert backend that HeyClicky (or Jarvis) calls when context is medical / longevity.
3. **Quant Mind** is the parallel specialist for markets.

### Concrete integration points

| Trigger | Flow |
|---------|------|
| Screen awareness | HeyClicky sees lab PDFs, wearables, Apple Health, CGM, doctor portals → hands text/OCR/context to Kyla analysis engine (opt-in capture; redaction required) |
| Voice + pointing | "What does this HbA1c trend mean for 10-year risk?" → Kyla returns structured risk framing + recommended *research* actions; HeyClicky speaks / annotates |
| Agent spawning | "Kyla Clicky" recurring job: e.g. Monday lab pull stub → biological-age score update → drift flag → morning briefing |
| Memory continuity | Shared `memory/` patient-like profile (local JSON/SQLite later) updated by Kyla; same store holds quant journal prefs |

## 2. Five-layer Jarvis architecture

```text
┌─────────────────────────────────────────────────────────────┐
│ INTERFACE     HeyClicky — voice, screen, point, type        │
├─────────────────────────────────────────────────────────────┤
│ ORCHESTRATOR  jarvis_orchestrator — route, approve, audit   │
├─────────────────────────────────────────────────────────────┤
│ SPECIALISTS   Kyla (health) · Quant Mind · code · research  │
├─────────────────────────────────────────────────────────────┤
│ MEMORY        memory/ — goals, prefs, health profile, journal│
├─────────────────────────────────────────────────────────────┤
│ EXECUTION     local agents · APIs · paper only · R13 gate   │
└─────────────────────────────────────────────────────────────┘
```

| Layer | Role | How HeyClicky + Kyla feed it |
|-------|------|------------------------------|
| Interface | Zero-friction I/O | HeyClicky voice + screen + pointing + typing |
| Orchestrator | Decide specialist | `jarvis` agent / ruflo; routes health → kyla-health, markets → quant-mind |
| Specialists | Deep competence | Kyla health agent; Quant Mind bridge to kyla-quant; Ollama fallback |
| Memory & state | Long-term personal model | `memory/profile.json` + room briefs; Clicky-scoped profiles later |
| Execution | Do the work | Computer-use stubs, calendars, lab *file* ingest — never silent live trade or clinical claim |

## 3. Routing rules (implemented)

- Keywords **lab, biomarker, HbA1c, CGM, longevity, biological age, wearable, apple health** → specialist `kyla-health` / room **R15**.
- Keywords **forex, signal, backtest, paper trade, risk, portfolio** → specialist `quant-mind` / room **R3**.
- Default ambient / UI commands → `heyclicky` bridge (echo + context packet for future screen agent).
- Everything else → existing ruflo / ollama / stack path.

## 4. Safety (non-negotiable)

- Medical outputs are **educational / research framing**, not diagnosis or treatment orders.
- Quant outputs are **paper / research only**.
- Screen capture and portal automation require explicit allowlist + R13.
- `runtime.dry_run: true` remains default; `--execute` for local specialists only.
- Secrets never in repo; health data stays local under `memory/` (gitignored patterns recommended).

## 5. CLI examples

```bash
# Interface packet (HeyClicky bridge)
python main.py --agent heyclicky --dry-run "annotate this lab PDF"

# Health specialist
python main.py --agent kyla-health --execute "interpret fasting glucose trend educational only"

# Quant specialist
python main.py --agent quant-mind --dry-run "paper scan EURUSD London session"

# Full orchestrator
python main.py --agent jarvis --execute "morning brief: health drift + paper portfolio pulse"
```

## 6. File map

| Path | Purpose |
|------|---------|
| `tools/heyclicky_bridge.py` | Interface layer stub: context packet, spawn hooks |
| `tools/kyla_health_agent.py` | Health/longevity specialist (local, disclaimer-heavy) |
| `tools/quant_mind_agent.py` | Bridge to quant workflows (paper) |
| `tools/jarvis_orchestrator.py` | Routes to specialists + memory |
| `memory/profile.example.json` | Template personal model |
| `memory/README.md` | Memory policy |
| `docs/JARVIS_HEYCLICKY_KYLA.md` | This document |

## 7. Next build steps (priority)

1. Real HeyClicky binary/extension hook (IPC or HTTP localhost).
2. OCR/PDF lab ingest → structured biomarkers in memory.
3. Recurring "Kyla Clicky" via system cron or ruflo schedule (still local).
4. Quant Mind live link to `kyla-quant` scripts without live order path.
5. Close LOOPHOLES.md items before any external webhook.
