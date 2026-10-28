# Sentinel

Sentinel is a small desktop helper for **XFCE on an X11 session**. It can send a screen capture and your question to a selected AI provider, show a tray menu, and save natural-language reminders locally. It does not claim Wayland support.

## Beginner installation (Linux Mint / Ubuntu)

Open Terminal. Run each block in order and wait for it to finish:

```sh
sudo apt update
sudo apt install -y git
```

```sh
git clone --branch main --depth 1 https://github.com/M3lcharagu/kyla-os.git
```

```sh
cd kyla-os/tools/sentinel
chmod +x setup.sh
./setup.sh
```

Run setup as your normal desktop user, **not with sudo**. It installs the system packages, creates `.venv`, installs Python requirements, copies `.env.example` to `.env` only when `.env` does not already exist, and registers Sentinel and its xbindkeys hotkeys for autostart. Existing `.env` credentials are preserved. Setup also runs the self-check; a missing API key is reported until you configure one.

### Add your provider key

Open `tools/sentinel/.env` in a text editor. Set `SENTINEL_PROVIDER` to `anthropic`, `openai`, or `gemini`, and fill in only the matching key variable (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `GEMINI_API_KEY`). Never share or commit this file. Log out and back in to start Sentinel and register the shortcuts.

## Self-check

From `kyla-os/tools/sentinel`, run:

```sh
.venv/bin/python sentinel.py --self-check
```

Each check prints `PASS` or `FAIL` and a one-line fix hint. It checks GTK/Python imports, DISPLAY/X11, `xset` and `xprintidle`, the selected provider key, opening the SQLite reminders database, and log writability. Run it again after fixing any reported issues.

## Shortcuts and use

After logging in, Sentinel appears in the tray. The global shortcuts are provided by xbindkeys:

| Shortcut | Action |
| --- | --- |
| Ctrl+Alt+C | Ask about the current screen |
| Ctrl+Alt+P | Create an action-plan response |
| Ctrl+Alt+S | Settings |
| Ctrl+Alt+L | View logs |
| Ctrl+Alt+Space | Pause / resume |
| Ctrl+Alt+Q | Quit |
| Super+Alt+R | Open the reminder input dialog |

A reminder can be entered in plain language, for example “remind me to call Sam tomorrow at 9am”. The selected provider interprets it into a title and timezone-aware due time; Sentinel stores it in SQLite and uses `notify-send` when it is due. Sentinel must be running and the computer awake at the due time.

The `.env` file supplies provider keys; the Settings dialog selects a provider and optional model override. Screenshots are retained only when retention is enabled in settings. Sentinel prunes the oldest files first to keep `logs/` plus retained screenshots within a combined 500 MiB limit. Local data is under `~/.local/share/sentinel/` by default.

## Troubleshooting

- **No tray icon:** Log out and back in after setup. Check that the XFCE panel includes a notification area/status-tray plugin. The process can still run if the panel does not display its icon. Inspect `~/.local/share/sentinel/logs/sentinel.log`.
- **A hotkey does nothing:** Confirm you are in XFCE on X11, log out and back in so the autostarted xbindkeys process loads the bindings, and check that another program is not using that shortcut. Verify `~/.config/sentinel/xbindkeysrc` and `~/.config/autostart/sentinel-hotkeys.desktop`; run `xbindkeys -n -f ~/.config/sentinel/xbindkeysrc` in a terminal to see xbindkeys errors (Ctrl+C stops that foreground test).
- **API error 401 / unauthorized:** Check that the key in `tools/sentinel/.env` is valid and belongs to the provider selected by `SENTINEL_PROVIDER` or Sentinel Settings. Remove accidental spaces and use the matching key variable. Never paste a key into logs or messages.
- **X11 vs Wayland:** This setup depends on X11-oriented desktop capture and hotkey tools. If `--self-check` reports Wayland or no DISPLAY, log into an XFCE X11 session instead. Wayland support is not claimed.
- **Missing commands or Python imports:** Run `./setup.sh` again, then `.venv/bin/python sentinel.py --self-check`. Fix any remaining `FAIL` item using its printed hint.
