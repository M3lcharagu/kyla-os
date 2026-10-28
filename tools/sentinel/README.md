# Sentinel

Sentinel is a small desktop helper for Linux Mint XFCE. It can describe what is on your screen, draft a step-by-step action plan, and help create reminders. It is designed for an **XFCE session running on X11**; the installer warns when the desktop session differs.

## Install

Open a terminal and run these lines **one at a time**, waiting for each to finish before entering the next. Start from your home folder. The setup script installs Sentinel's system and Python dependencies and prepares its desktop startup and keyboard shortcuts.

```text
sudo apt update
```

```text
sudo apt install --yes git
```

```text
git clone --branch main --depth 1 https://github.com/M3lcharagu/kyla-os.git
```

```text
cd kyla-os/tools/sentinel
```

```text
chmod +x setup.sh
```

```text
./setup.sh
```

Run setup as your usual desktop user, **not as root**. It creates a local `.env` file from `.env.example` if one is not already there. After setup, add your provider and API key as described below, then log out and back in to XFCE. Setup installs Sentinel and its hotkey launcher in the desktop autostart folder, so it starts when you log in.

### A local setup fix to know about

The checked-in `sentinel.py` source still has two issues: it uses `signal` without importing it, and its empty reminder hotkey request does not open the reminder dialog. The setup script applies those two small fixes **to the local clone's `sentinel.py` during installation**. It keeps a backup at `~/.local/share/sentinel/backups/sentinel.py.before-setup` when it applies the patch. This does not patch the GitHub source or create a source-code commit; the repository source remains unpatched.

## Choose an API provider and add your key

Sentinel supports three providers. Create a key with the provider you choose:

| Provider | Create a key | Provider setting | Key variable in `.env` |
| --- | --- | --- | --- |
| Anthropic | [console.anthropic.com](https://console.anthropic.com/) | `anthropic` | `ANTHROPIC_API_KEY` |
| OpenAI | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | `openai` | `OPENAI_API_KEY` |
| Google Gemini | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) | `gemini` | `GEMINI_API_KEY` |

Open `tools/sentinel/.env` in a text editor. Set `SENTINEL_PROVIDER` to the provider name in the table, and paste the key into the matching key variable. Fill in only the provider key you plan to use. You can also select a provider in Sentinel's **Settings** menu and optionally enter a model override; leaving the model blank uses that provider's built-in default. Keep the `.env` provider setting and the Settings choice aligned: `SENTINEL_PROVIDER` in `.env` takes precedence when Sentinel starts. The example file starts with `SENTINEL_PROVIDER=anthropic`.

**Never put an API key in a repository file or share it in a screenshot.** The repository ignores `.env` and `.env.*` (while keeping `.env.example`), and setup preserves an existing `.env`. Your key is read locally from `.env` or the process environment. Sentinel sends the captured screen image and your request to the selected provider for processing, so do not use it on a screen you do not want to send to that provider.

## Use Sentinel

After logging back in, look for Sentinel in the desktop's tray area. Its configured global shortcuts are:

| Shortcut | What it does |
| --- | --- |
| `Ctrl` + `Alt` + `C` | Capture the screen and ask for help or a description. |
| `Ctrl` + `Alt` + `P` | Capture the screen and ask for an action plan. |
| `Ctrl` + `Alt` + `S` | Open Settings. Choose a provider, optionally set a model override, and choose whether to keep processed screenshots. |
| `Ctrl` + `Alt` + `L` | View the Sentinel log. |
| `Ctrl` + `Alt` + `Space` | Pause or resume processing. |
| `Ctrl` + `Alt` + `Q` | Quit Sentinel. |
| `Ctrl` + `Alt` + `R` | Open the reminder dialog. |

You can also use the tray menu for capture, action plans, reminders, Settings, logs, pause/resume, and quit. An action plan is shown for review first. It runs only after you choose **Confirm and run plan**; dismissing it leaves the actions unrun. Shell commands must exactly match a line in the safety allowlist. That list is empty by default, so shell-command steps are blocked unless you deliberately add an exact command. Destructive shell commands that are allowed require another confirmation. Review every proposed step before confirming, including keyboard and mouse actions.

For a reminder, enter a plain-language request, such as “remind me to call Sam tomorrow at 9am,” and choose **Parse and save**. Sentinel asks the selected provider to interpret the time, saves the reminder locally, and uses a desktop notification when it is due. The computer must be on and Sentinel running for its reminder check to run.

## Screenshots, logs, and storage

Sentinel captures a screenshot for each screen request and sends it to the selected provider. By default, the local screenshot file is deleted after the request finishes, including when a request fails. Turn on **Keep screenshots after processing** in Settings only if you want those local image files retained. Screenshots are stored under `~/.local/share/sentinel/screenshots/`.

Sentinel prunes older files in its data folder toward a **500 MB** limit. It skips the active log and reminder database while pruning, so those protected files can leave the folder above the target. Logs are under `~/.local/share/sentinel/`; the tray's **View log** item opens the log viewer. Settings and reminder data are stored locally as well.

## Troubleshooting

- **No tray icon:** Log out and back in after setup. Sentinel's tray-icon setup can fail while the process continues, so a missing icon alone does not prove it stopped. Check whether the desktop panel is showing its tray/status icons. If needed, open `~/.local/share/sentinel/sentinel.log` in a text editor to look for startup or tray errors.
- **A shortcut does nothing:** The shortcuts are registered by the installed `xbindkeys` launcher. Log out and back in after setup, check that you are in XFCE on X11, and check for another application using the same shortcut. The setup script is aimed at XFCE/X11; it does not promise working global shortcuts in other sessions.
- **API error 401 / unauthorized:** Check that the key is active and belongs to the provider selected in Settings and `SENTINEL_PROVIDER`. Confirm that the matching variable (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `GEMINI_API_KEY`) in `.env` contains the key, with no accidental spaces. Do not post the key in logs, screenshots, or messages.
- **You are using Wayland:** Setup is aimed at XFCE on X11. Global shortcuts and screen/input actions rely on X11-oriented tools, so they may not work in a Wayland session. Sign in to an XFCE X11 session for the setup described here; Wayland support is not claimed.
