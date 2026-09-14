# KYLA OS · 3D Mansion

A fast, dependency-light night penthouse starter for KYLA OS. The experience is a single static `index.html` using [A-Frame](https://aframe.io/) from its CDN—there is no bundler, install step, asset pipeline, or local build output.

## Run locally

The file can be opened directly in a browser:

```text
web/mansion/index.html
```

An HTTP server is recommended for the closest match to a hosted deployment:

```bash
python3 -m http.server 8000 --directory web/mansion
```

Then open <http://localhost:8000>. The A-Frame CDN requires an internet connection when the page loads; the mansion itself has no other external assets.

## GitHub Pages (free)

1. Push this repository to GitHub.
2. In **Settings → Pages**, choose **Deploy from a branch**.
3. Select `main` and the repository root (`/`), then save.
4. Open the published repository URL and append `/web/mansion/`.

For a project site, the resulting path is normally:

```text
https://YOUR-ACCOUNT.github.io/YOUR-REPOSITORY/web/mansion/
```

GitHub Pages serves the static file directly; no build command is needed. If you want the mansion at the site root instead, set the Pages source to a branch/folder that contains this folder's contents, or copy the two files into the selected publishing directory.

## Vercel free tier

### Dashboard

1. Import the repository into Vercel.
2. Choose **Other** (or leave the framework preset unselected).
3. Leave **Build Command** empty.
4. Set **Output Directory** to `web/mansion`.
5. Deploy.

### CLI

From the repository root:

```bash
npx vercel --cwd web/mansion
```

No paid features, server runtime, environment variables, or build step are required. The result is a static deployment and `index.html` is served automatically.

## Interaction

- Click a glowing door or use the 14-button navigation panel to select a space.
- Desktop mouse input is handled by A-Frame's camera cursor and raycaster.
- `WASD` / arrow keys move the camera; drag to look around.
- The 2D SOPHIA overlay reports the selected node and keeps navigation available on small screens.

The mansion contains: R1 HUMANITAS Command Center, R2 PATIENTIA Second Brain, R3 TEMPERANTIA Trading Room, R4 INDUSTRIA Dev Lab, R5 LUXURIA Creative Studio, R6 GULA Editing Suite, R7 SUPERBIA Broadcast Room, R8 INVIDIA Photo Studio, R9 CARITAS Client Lounge, R10 HUMILITAS Study Room, R11 AVARITIA Business Ops, R12 ACEDIA Research & Intelligence, R13 IRA QA & Security, and R14 CASTITAS Life OS.
