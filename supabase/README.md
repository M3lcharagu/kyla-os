# KYLA × Supabase (free tier) — database + logins

Supabase is KYLA's **default backend**. It is *default-on but lazy*: until you add the keys,
everything keeps working exactly as before (web UI uses `localStorage`, Actions just write
files). Nothing is installed locally — no Docker, no Supabase CLI required.

| Piece | What it does | Key it uses |
|---|---|---|
| `web/supabase.js` | Magic-link login, syncs chats / tasks / agent runs when signed in | Project URL + **anon / publishable** key (public-safe) |
| `tools/supabase_sink.py` | Bridge + GitHub Actions write `agent_runs` and `news_briefs` (stdlib REST, no deps) | Project URL + **service_role / secret** key (private) |
| `.github/workflows/supabase-keepalive.yml` | Cheap REST select Mon + Thu so the free project doesn't pause | same private key (GitHub secret) |
| `migrations/0001_kyla_core.sql` | Tables + Row Level Security | — |

## Tables (all with Row Level Security ON)

| Table | Purpose |
|---|---|
| `profiles` | One row per login (linked to `auth.users`). First account to sign in = `is_owner` |
| `agent_runs` | agent, room, status, input, output, source (web / bridge / actions), started/finished |
| `chat_messages` | Command-center chat history |
| `tasks` | Tasks and notes (`kind = task | note`, `status = todo | doing | done`) |
| `memories` | Key / value memory (`unique(user_id, key)`) |
| `store_leads` | KYLA store orders / leads: product, price, currency (KES), contact, source, status |
| `news_briefs` | Daily brief markdown from the `KYLA Daily News Brief` workflow |

Policies: signed-in users can only read/write **their own rows** (`auth.uid() = user_id`).
Rows written by Actions / the bridge use the service key (bypasses RLS) and have
`user_id = NULL`; only the **owner** account can read those. Logged-out visitors get nothing.

## Setup (≈10 minutes, free)

1. **Create the project** — go to <https://supabase.com>, sign in with GitHub, **New project**,
   plan **Free**, name `kyla`, pick the closest region (there is no Africa region; an EU region
   such as Frankfurt or London is fine from Nairobi), set a database password (save it).
2. **Create the tables** — Dashboard → **SQL Editor** → *New query* → paste all of
   [`migrations/0001_kyla_core.sql`](migrations/0001_kyla_core.sql) → **Run**.
   It is safe to re-run.
   *(Optional CLI route: `supabase link --project-ref <ref>` then `supabase db push`.)*
3. **Allow the login redirect** — Dashboard → **Authentication → URL Configuration**:
   - Site URL: `https://m3lcharagu.github.io/kyla-os/web/`
   - Redirect URLs: add `https://m3lcharagu.github.io/kyla-os/**` and `http://localhost:8080/**`
     (for `make ui`). Email (magic link) login is on by default.
4. **Copy 3 values** — Dashboard → **Connect** (or Project Settings → API Keys):
   1. **Project URL** — `https://<ref>.supabase.co`
   2. **anon key** (or the newer **publishable** key `sb_publishable_…`) — public-safe
   3. **service_role key** (or the newer **secret** key `sb_secret_…`) — private, bypasses RLS

   Supabase is phasing out the legacy `anon` / `service_role` keys in favour of
   publishable / secret keys; KYLA accepts either format.
5. **Put them in the right places**

   | Value | Where |
   |---|---|
   | Project URL | GitHub → repo **Settings → Secrets and variables → Actions** → secret `SUPABASE_URL` |
   | service_role / secret key | same place → secret `SUPABASE_SERVICE_ROLE_KEY` |
   | Project URL + anon / publishable key | `web/config.js` → `KYLA_SUPABASE_URL` + `KYLA_SUPABASE_ANON_KEY` (commit; public-safe) **or** paste them in the UI: account badge → *Supabase settings* (saved in that browser only) |
   | URL + service key for the bridge | `.env` in the repo root on the bridge host (copy `.env.example`; never commit `.env`) |

   **Never** put the service_role / secret key in `web/` — the UI refuses it and the
   `KYLA PR Check` workflow fails if one shows up there.
6. **Sign in** — open <https://m3lcharagu.github.io/kyla-os/web/>, tap the account badge
   (top right), enter your email, open the magic link on the same device. The first account
   that signs in becomes the owner (can read Actions / bridge rows).
7. **Test** — Actions → *KYLA Daily News Brief* → **Run workflow**, then check
   Table Editor → `news_briefs`. Actions → *Supabase Keep-Alive* → **Run workflow** should say HTTP 200.
   Locally: `python tools/integrations_cli.py run supabase ping`.

## Free tier — honest limits

- **50,000 monthly active users** and a **500 MB database** — plenty for one person.
- **Free projects pause after about 1 week of inactivity.** The daily brief writes and the
  twice-weekly keep-alive workflow keep it active. If it does pause, open the dashboard and
  click *Restore project*; KYLA keeps working in local mode meanwhile (all writes are soft).
- The built-in email sender is rate-limited (about **2 auth emails per hour** per project).
  Fine for your own logins; add custom SMTP later if you ever need more.
- Up to 2 free projects per account.

## Using it from KYLA

- Web command center: normal chat is saved automatically when signed in.
  `/task <text>`, `/note <text>`, `/tasks` manage tasks; tap a task in the focus panel to finish it.
- Server / Actions:
  ```bash
  python3 tools/supabase_sink.py status
  python3 tools/supabase_sink.py ping
  python3 tools/supabase_sink.py brief --date 2026-09-25 --file kyla/briefs/2026-09-25.md
  python3 tools/supabase_sink.py run --agent kyla-daily --status ok --input "daily" --output-file out.md
  ```
  Every command exits 0 and prints "not configured — skipping" when keys are missing.
