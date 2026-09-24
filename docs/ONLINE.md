# KYLA online — 24/7 without Melvin's laptop

**Short answer: YES.** Bots can run 24/7 online with zero intervention, on free paths.

There are **two different “online” modes**. Both are free. Neither needs Melvin's Mac for day-to-day.

| Mode | What it does | Who keeps it alive | Melvin needed? |
|------|----------------|--------------------|----------------|
| **Scheduled (batch)** | Daily brief, stack-health, repo-digest, ruflo-health | **GitHub Actions cron** | **No** |
| **Interactive (chat)** | Phone/browser talks to room bots and gets live replies | **Always-on bridge host** (Grok Bot box now → free VPS later → Mac localhost later) | Only to keep that host/tunnel up |

Pages UI is static: https://m3lcharagu.github.io/kyla-os/web/

---

## 1) Scheduled = GitHub Actions (true zero-touch)

These workflows already run on a schedule. After this PR lands, push races are fixed (shared `concurrency` + rebase retry) so crons stay green:

| Workflow | Cron (UTC) | ~EAT | Purpose |
|----------|------------|------|----------|
| `kyla-daily.yml` | `0 4 * * *` | 07:00 | News / market brief → `kyla/briefs/` |
| `kyla-stack-health.yml` | `0 3 * * *` | 06:00 | Dry-run routes + catalog digest |
| `kyla-repo-digest.yml` | `30 4 * * *` | 07:30 | Commit/tree digest (no LLM) |
| `ruflo-health.yml` | (see file) | — | Ruflo wiring smoke |

**Melvin does nothing.** Open the Actions tab to watch. Manual run: Actions → workflow → **Run workflow**.

Batch agent runs (ad-hoc): Actions → **Kyla Run** → pick room/agent/prompt → download `kyla-reply` artifact.

Agents on Actions (free): `ruflo` (default; falls through if Node/npx cold), `stack`, `agent-reach` (if CLI present), `ollama` (hint-only on runners), `shell` / `echo`, `clip`.

---

## 2) Interactive = online bridge host (phone chat)

Static Pages **cannot** hold GitHub tokens. Live chat needs a tiny API:

```bash
# on always-on host (Grok Bot computer right now)
cd kyla-os
python tools/online_bridge.py          # http://127.0.0.1:8787
cloudflared tunnel --url http://127.0.0.1:8787
```

Then put the `https://….trycloudflare.com` URL into `web/config.js`:

```js
window.KYLA_API = "https://YOUR-TUNNEL.trycloudflare.com";
```

Reload the Pages UI on your phone. Room orbs + command dock call `POST /v1/run` and show the reply.

Endpoints:

- `GET /v1/health`
- `GET /v1/stack`
- `POST /v1/run` `{ "room", "agent", "prompt" }`

CORS is open for `*.github.io` and localhost.

**Do not commit ephemeral tunnel URLs to `main`.** Put them in `/workspace/KYLA_ONLINE_HANDOFF.md` (or your notes). Sample: `web/config.online.js.sample`.

### Host progression (still free)

1. **Now:** Grok Bot box runs bridge + cloudflared.
2. **Later:** any free/cheap always-on VPS (Oracle free tier, etc.).
3. **Mac later:** when Catalina/Ollama is ready, point `KYLA_API` at `http://127.0.0.1:8787` (or LAN IP) and skip the tunnel for home use.

---

## Phone checklist (today)

1. Open https://m3lcharagu.github.io/kyla-os/web/
2. Look at the **Online / Offline** badge.
3. If **Online**: tap a room bot → type a prompt → get a real reply.
4. If **Offline**: tap **connect** for one-click instructions, or use Actions → Kyla Run for batch.
5. Scheduled briefs keep writing themselves every morning either way.

---

## Local-later (Mac)

```bash
bash scripts/setup_local.sh
python tools/online_bridge.py
# optional UI:
make ui
# set window.KYLA_API = "http://127.0.0.1:8787" in web/config.js
```

Ollama on Catalina 8GB stays `$0`. Ruflo stays default orchestrator when Node 20 is present (nvm).

---

## Honesty

- **24/7 scheduled agents = YES, free, zero Melvin** (Actions).
- **24/7 interactive chat = YES, free**, as long as *some* host keeps `online_bridge` + tunnel up (Grok Bot / VPS). Not Melvin's sleeping laptop.
- Pages alone = pretty UI only. Bridge or Actions = real brain.
