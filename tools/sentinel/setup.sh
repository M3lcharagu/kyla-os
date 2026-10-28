#!/usr/bin/env bash
# Install Sentinel for an XFCE desktop session on X11. Run as a normal user.
set -Eeuo pipefail
umask 077
APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
APP="$APP_DIR/sentinel.py"
VENV="$APP_DIR/.venv"
ENV_FILE="$APP_DIR/.env"
CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/sentinel"
AUTOSTART="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
HOTKEYS="$CONFIG/xbindkeysrc"
[[ ${EUID:-$(id -u)} -ne 0 ]] || { echo 'Run as your normal desktop user, not root.' >&2; exit 1; }
[[ -f "$APP" && -f "$APP_DIR/.env.example" && -f "$APP_DIR/requirements.txt" ]] || { echo "Missing Sentinel source, .env.example, or requirements.txt in $APP_DIR" >&2; exit 1; }
command -v sudo >/dev/null || { echo 'sudo is required to install apt packages.' >&2; exit 1; }
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip python3-gi python3-gi-cairo gir1.2-gtk-3.0 xbindkeys xdotool x11-xserver-utils xprintidle libnotify-bin
if [[ ! -x "$VENV/bin/python" ]]; then python3 -m venv --system-site-packages "$VENV"; fi
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install -r "$APP_DIR/requirements.txt" requests mss
if [[ ! -e "$ENV_FILE" ]]; then install -m 600 "$APP_DIR/.env.example" "$ENV_FILE"; echo "Created $ENV_FILE; add your provider API key."; fi
mkdir -p "$CONFIG" "$AUTOSTART"
# xbindkeys command quoting protects user paths containing spaces or quotes.
q() { local s="$1"; s="${s//\\/\\\\}"; s="${s//\"/\\\"}"; printf '"%s"' "$s"; }
PY="$VENV/bin/python"
printf '# Sentinel shortcuts (XFCE/X11); managed by setup.sh.\n\n%s %s --capture\n  Control+Alt + c\n\n%s %s --plan\n  Control+Alt + p\n\n%s %s --settings\n  Control+Alt + s\n\n%s %s --logs\n  Control+Alt + l\n\n%s %s --pause\n  Control+Alt + space\n\n%s %s --quit\n  Control+Alt + q\n\n%s %s --remind ""\n  Mod4+Alt + r\n' "$(q "$PY")" "$(q "$APP")" "$(q "$PY")" "$(q "$APP")" "$(q "$PY")" "$(q "$APP")" "$(q "$PY")" "$(q "$APP")" "$(q "$PY")" "$(q "$APP")" "$(q "$PY")" "$(q "$APP")" "$(q "$PY")" "$(q "$APP")" > "$HOTKEYS"
chmod 600 "$HOTKEYS"
XBINDS="$(command -v xbindkeys)"
printf '[Desktop Entry]\nType=Application\nName=Sentinel\nComment=Start the Sentinel desktop helper\nExec="%s" "%s" --daemon\nTerminal=false\nX-GNOME-Autostart-enabled=true\n' "$PY" "$APP" > "$AUTOSTART/sentinel.desktop"
printf '[Desktop Entry]\nType=Application\nName=Sentinel hotkeys\nComment=Register Sentinel keyboard shortcuts\nExec="%s" -f "%s"\nTerminal=false\nX-GNOME-Autostart-enabled=true\n' "$XBINDS" "$HOTKEYS" > "$AUTOSTART/sentinel-hotkeys.desktop"
chmod 600 "$AUTOSTART/sentinel.desktop" "$AUTOSTART/sentinel-hotkeys.desktop"
printf 'Setup files installed. Log out and back in to start Sentinel and its shortcuts.\n\nRunning Sentinel self-check:\n'
"$PY" "$APP" --self-check
