#!/usr/bin/env bash
# Install Sentinel for Linux Mint 22.3 with Xfce on X11.
# Run from a terminal with: bash tools/sentinel/setup.sh
set -Eeuo pipefail
umask 077

APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
APP_FILE="$APP_DIR/sentinel.py"
VENV="$APP_DIR/.venv"
ENV_FILE="$APP_DIR/.env"
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
SENTINEL_CONFIG="$CONFIG_HOME/sentinel"
AUTOSTART="$HOME/.config/autostart"
HOTKEYS="$SENTINEL_CONFIG/xbindkeysrc"

fail() { printf 'Sentinel setup: %s\n' "$*" >&2; exit 1; }

[[ ${EUID:-$(id -u)} -ne 0 ]] || fail 'Run as your normal desktop user, not as root.'
[[ -f "$APP_FILE" ]] || fail "Cannot find the existing app: $APP_FILE"
for required in requirements.txt .env.example safety.allowlist; do
    [[ -f "$APP_DIR/$required" ]] || fail "Missing required file: $APP_DIR/$required"
done

if [[ -r /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    if [[ "${ID:-}" != linuxmint || "${VERSION_ID:-}" != 22.3 ]]; then
        printf 'Note: this setup targets Mint 22.3; detected %s %s.\n' "${ID:-unknown}" "${VERSION_ID:-unknown}" >&2
    fi
fi
if [[ "${XDG_CURRENT_DESKTOP:-}" != *XFCE* || "${XDG_SESSION_TYPE:-}" != x11 ]]; then
    printf 'Note: persistent hotkeys/autostart are configured for an Xfce X11 login.\n' >&2
fi

command -v sudo >/dev/null 2>&1 || fail 'sudo is required to install system packages.'
sudo apt-get update
sudo apt-get install -y \
    python3 python3-venv python3-pip \
    python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-gdkpixbuf-2.0 \
    xbindkeys xdotool x11-xserver-utils xprintidle libnotify-bin

# This source commit omits signal and ignores an empty reminder request.
# Apply only these verified, idempotent fixes; save a one-time backup first.
python3 - "$APP_FILE" <<'PY'
import ast
import os
import re
import shutil
import stat
import sys
import tempfile
from pathlib import Path

path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
updated = source
if "signal.signal(" in updated and not re.search(
    r"(?m)^\s*(?:import\s+[^#\n]*\bsignal\b|from\s+signal\s+import\b)", updated
):
    if "import base64" not in updated:
        raise SystemExit("Cannot safely add the missing signal import; source layout changed.")
    updated = updated.replace("import base64", "import signal\nimport base64", 1)

old = "elif a=='remind': self.add_reminder(str(r.get('text','')).strip())"
new = "elif a=='remind':\n            text=str(r.get('text','')).strip()\n            if text: self.add_reminder(text)\n            else: self.reminder_dialog()"
if old in updated:
    updated = updated.replace(old, new, 1)
elif new not in updated:
    raise SystemExit("Cannot safely enable the empty-reminder dialog; source layout changed.")

if updated != source:
    ast.parse(updated, filename=str(path))
    backup_dir = Path.home() / ".local/share/sentinel/backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / "sentinel.py.before-setup"
    if not backup.exists():
        shutil.copy2(path, backup)
    mode = stat.S_IMODE(path.stat().st_mode)
    fd, temporary = tempfile.mkstemp(prefix=".sentinel.py.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(updated)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print("Applied verified Sentinel source fixes; backup saved under ~/.local/share/sentinel/backups.")
PY

if [[ ! -e "$VENV/bin/python" ]]; then
    [[ ! -e "$VENV" ]] || fail "$VENV exists but is not a usable virtual environment; inspect it before changing it."
    python3 -m venv --system-site-packages "$VENV"
fi
"$VENV/bin/python" -c 'import gi' >/dev/null 2>&1 || fail 'The existing venv cannot import system PyGObject. Keep it safe; inspect/recreate it manually with --system-site-packages.'
PIP_DISABLE_PIP_VERSION_CHECK=1 "$VENV/bin/python" -m pip install -r "$APP_DIR/requirements.txt"

# Never replace a user's existing credentials or approved-command list.
if [[ -e "$ENV_FILE" || -L "$ENV_FILE" ]]; then
    [[ -f "$ENV_FILE" ]] || fail "$ENV_FILE exists but is not a regular file; leaving it untouched."
    printf 'Preserving existing %s\n' "$ENV_FILE"
else
    install -m 600 "$APP_DIR/.env.example" "$ENV_FILE"
    printf 'Created %s from .env.example; edit it to add your own provider key.\n' "$ENV_FILE"
fi
mkdir -p "$SENTINEL_CONFIG" "$AUTOSTART"
if [[ ! -e "$SENTINEL_CONFIG/safety.allowlist" ]]; then
    install -m 600 "$APP_DIR/safety.allowlist" "$SENTINEL_CONFIG/safety.allowlist"
fi

# xbindkeys uses a dedicated config file and autostart entry, so reruns do not
# overwrite ~/.xbindkeysrc or any user's unrelated Xfce shortcuts.
XBINDS="$(command -v xbindkeys)"
PYTHON="$VENV/bin/python"
shell_arg() { printf '%q' "$1"; }
desktop_arg() {
    local value="$1"
    value=${value//\\/\\\\}
    value=${value//\"/\\\"}
    value=${value//%/%%}
    printf '"%s"' "$value"
}

cat > "$HOTKEYS" <<EOF
# Generated by tools/sentinel/setup.sh. Safe to regenerate; dedicated to Sentinel.
$(shell_arg "$PYTHON") $(shell_arg "$APP_FILE") --capture
  Control+Alt + c

$(shell_arg "$PYTHON") $(shell_arg "$APP_FILE") --plan
  Control+Alt + p

$(shell_arg "$PYTHON") $(shell_arg "$APP_FILE") --settings
  Control+Alt + s

$(shell_arg "$PYTHON") $(shell_arg "$APP_FILE") --logs
  Control+Alt + l

$(shell_arg "$PYTHON") $(shell_arg "$APP_FILE") --pause
  Control+Alt + space

$(shell_arg "$PYTHON") $(shell_arg "$APP_FILE") --quit
  Control+Alt + q

$(shell_arg "$PYTHON") $(shell_arg "$APP_FILE") --remind \"\"
  Control+Alt + r
EOF
chmod 600 "$HOTKEYS"

cat > "$AUTOSTART/sentinel.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Sentinel
Comment=Start the Sentinel desktop assistant
Exec=$(desktop_arg "$PYTHON") $(desktop_arg "$APP_FILE") --daemon
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

cat > "$AUTOSTART/sentinel-hotkeys.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Sentinel hotkeys
Comment=Register Sentinel keyboard shortcuts with xbindkeys
TryExec=$(desktop_arg "$XBINDS")
Exec=$(desktop_arg "$XBINDS") -f $(desktop_arg "$HOTKEYS")
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
chmod 600 "$AUTOSTART/sentinel.desktop" "$AUTOSTART/sentinel-hotkeys.desktop"
printf '\nSentinel setup is complete. Log out and back in to start Sentinel and its hotkeys.\n'
printf 'Hotkeys: Ctrl+Alt+C capture, P plan, S settings, L logs, Space pause, Q quit, R reminder dialog.\n'
