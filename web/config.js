/* KYLA online config — committed default is empty (demo/offline Pages).
 * For live interactive bots, set KYLA_API to the online bridge URL
 * (cloudflared public URL or http://127.0.0.1:8787 when local).
 * See docs/ONLINE.md and web/config.online.js.sample
 */
window.KYLA_API = window.KYLA_API || "";
window.KYLA_DISPATCH_URL = window.KYLA_DISPATCH_URL || ""; // optional Actions proxy later
window.KYLA_DEFAULT_AGENT = window.KYLA_DEFAULT_AGENT || "ruflo";
window.KYLA_DEFAULT_ROOM = window.KYLA_DEFAULT_ROOM || "R1";

/* Supabase (optional, free tier) — cloud sync + magic-link login. Leave empty = local mode.
 * Paste your Project URL + the ANON / PUBLISHABLE key (public-safe; RLS protects data).
 * NEVER put the service_role / sb_secret_ key here. You can also set these from the
 * Account panel in the UI (stored in this browser only). See supabase/README.md.
 */
window.KYLA_SUPABASE_URL = window.KYLA_SUPABASE_URL || "";
window.KYLA_SUPABASE_ANON_KEY = window.KYLA_SUPABASE_ANON_KEY || "";
