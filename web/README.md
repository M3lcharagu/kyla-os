# KYLA Web

A phone-first, no-build static dashboard for a personal AI command center. The visual language is a dark Kilimani penthouse at dusk: elegant, cinematic, and slightly adult-animation-inspired without using protected characters or assets.

## Vercel free-tier deployment

1. Import `M3lcharagu/kyla-os` in [Vercel](https://vercel.com/new).
2. Set **Root Directory** to `web`.
3. Leave **Framework Preset** as `Other`.
4. Leave **Build Command** empty and set **Output Directory** to `.`.
5. Deploy. Vercel serves `web/index.html` directly; there are no dependencies or build steps.

Alternatively, deploy from the repository root with the Vercel CLI using `vercel web`.

## Astra 3D integration

The visual-lab scene is intentionally dependency-free. Add an Astra embed URL to the `data-scene-url` attribute on `.scene-card` in `index.html`:

```html
<div class='card scene-card' data-scene-url='https://your-astra-embed.example/scene'>
```

`app.js` copies that URL into the marked iframe at runtime. With the attribute empty, the accessible placeholder remains visible. If the scene is unavailable, use the adjacent fallback panel and place a compatible asset at `/assets/astra.glb`; this scaffold keeps the GLB path as a clear integration hand-off without adding a heavy viewer.

## Local preview

Open `web/index.html` directly for the static preview, or run any simple static server from the `web` directory, for example `python3 -m http.server 8080`.

## Supabase login + sync (optional)

`supabase.js` adds magic-link login and cloud sync. Set `KYLA_SUPABASE_URL` and
`KYLA_SUPABASE_ANON_KEY` in `config.js` (anon / publishable key only — public-safe), or paste
them into the account panel (top-right badge → *Supabase settings*). Without them the UI stays
in local mode and loads nothing extra. `supabase-js` comes from jsDelivr (esm.sh fallback) via
dynamic `import()`, so there is still no build step. See `../supabase/README.md`.

## Notes

- Weather is a lightweight local mock that rotates a few Nairobi-friendly states by day; no API key or network request is required.
- Chat talks to the online bridge when `?api=` / `KYLA_API` is set; history persists to Supabase when signed in, else `localStorage`.
- All visuals are CSS and inline text; no framework, package manager, or protected character artwork is used.
