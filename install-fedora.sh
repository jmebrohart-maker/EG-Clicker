#!/usr/bin/env bash
# EG-Clicker Fedora 44 KDE Wayland per-user installer
set -Eeuo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
fail(){ echo; echo "INSTALL FAILED: $*" >&2; echo 'Press Enter to close.'; read -r _ || true; exit 1; }
trap 'echo "Installer stopped at line $LINENO (exit code $?)." >&2' ERR

printf '\n===== EG-Clicker • Fedora 44 KDE Wayland =====\n\n'
[[ -r "$HERE/EG-Clicker.py" && -r "$HERE/eg_platform.py" && -r "$HERE/launcher.py" ]] || fail "EG-Clicker.py, eg_platform.py and launcher.py must be beside the installer. Extract the ZIP first."
[[ -r "$HERE/eg_logo_icon.png" ]] || fail 'Missing icon file; extract entire ZIP.'
[[ $(id -u) != 0 ]] || fail 'Run as your desktop user, not as root.'
[[ ${XDG_SESSION_TYPE:-} == wayland ]] || fail 'Log into KDE Plasma Wayland, then run this installer.'
[[ -e /etc/fedora-release ]] || fail 'This installer is for Fedora Linux.'
FEDORA_VER="$(rpm -E '%fedora')"
[[ $FEDORA_VER == 44 ]] || fail "Expected Fedora 44, found Fedora $FEDORA_VER."
for binary in dnf curl python3; do command -v "$binary" >/dev/null || fail "Missing system command $binary"; done
command -v pkexec >/dev/null || fail 'polkit pkexec not found. Install polkit or use an admin account.'

PKGS=(python3 python3-tkinter pulseaudio-utils kdotool libkscreen xdg-desktop-portal-kde curl)
# Pinned waytool release. Require upstream GitHub immutable SHA-256 digest.
# Security caveat: the digest is fetched from GitHub, not independently baked in.
WAYTOOL_VERSION='v1.0.1'
TMPDIR_EG="$(mktemp -d)"
trap 'rm -rf -- "$TMPDIR_EG"' EXIT
RPM_FILE=""
if [[ ! -x /usr/bin/waytool ]]; then
  ARCH="$(uname -m)"
  case "$ARCH" in x86_64|aarch64) ;; *) fail "Unsupported architecture $ARCH";; esac
  META="$TMPDIR_EG/release.json"
  curl -fsSL --retry 3 --connect-timeout 15 --max-time 50 \
    "https://api.github.com/repos/mx-shift/waytool/releases/tags/$WAYTOOL_VERSION" \
    -o "$META" || fail 'Pinned waytool release metadata unavailable.'
  RPM_FILE="$TMPDIR_EG/waytool-$WAYTOOL_VERSION.fc44.$ARCH.rpm"
  readarray -t ASSET < <(/usr/bin/python3 - "$META" "$ARCH" "$WAYTOOL_VERSION" <<'PYMETA'
import json, re, sys
obj=json.load(open(sys.argv[1]))
expected=f'waytool-{sys.argv[3].removeprefix("v")}-1.fc44.{sys.argv[2]}.rpm'
assets=[a for a in obj.get('assets',[]) if a.get('name')==expected]
if len(assets)!=1 or obj.get('tag_name')!=sys.argv[3]:
    raise SystemExit('Pinned release or asset missing')
a=assets[0]
digest=a.get('digest') or ''
url=a.get('browser_download_url') or ''
if not re.fullmatch('sha256:[a-fA-F0-9]{64}',digest):
    raise SystemExit('Missing SHA-256 digest; refusing unverified RPM')
if url!=f'https://github.com/mx-shift/waytool/releases/download/{sys.argv[3]}/{expected}':
    raise SystemExit('Unexpected release URL')
print(url)
print(digest.removeprefix('sha256:'))
PYMETA
  ) || fail 'Release verification metadata rejected.'
  [[ ${#ASSET[@]} -eq 2 && ${ASSET[1]} =~ ^[a-fA-F0-9]{64}$ ]] || fail 'No trusted checksum in release metadata.'
  curl -fL --retry 3 --connect-timeout 15 --max-time 240 -o "$RPM_FILE" "${ASSET[0]}" || fail 'waytool download failed.'
  printf '%s  %s\n' "${ASSET[1]}" "$RPM_FILE" | /usr/bin/sha256sum --check --status || fail 'RPM checksum mismatch. Aborting.'
  printf 'Pinned waytool %s RPM SHA-256 verified.\n' "$WAYTOOL_VERSION"
fi

echo
printf 'Dependency installation requires a Fedora administrator authorization dialog.\n'
if [[ -n "$RPM_FILE" ]]; then
  pkexec /usr/bin/dnf install -y "${PKGS[@]}" "$RPM_FILE" || fail 'dnf package installation was denied or failed.'
else
  pkexec /usr/bin/dnf install -y "${PKGS[@]}" || fail 'dnf package installation was denied or failed.'
fi
[[ -x /usr/bin/waytool ]] || fail 'waytool not found after dependency installation.'

DEST="$HOME/.local/share/eg-clicker"
mkdir -p -m 0700 "$DEST" "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/96x96/apps"
install -m 0644 "$HERE/EG-Clicker.py" "$DEST/EG-Clicker.py"
install -m 0644 "$HERE/launcher.py" "$DEST/launcher.py"
install -m 0644 "$HERE/eg_platform.py" "$DEST/eg_platform.py"
install -m 0700 "$HERE/uninstall-fedora.sh" "$DEST/uninstall-fedora.sh"
install -m 0644 "$HERE/eg_logo_icon.png" "$HOME/.local/share/icons/hicolor/96x96/apps/eg-clicker.png"

# Exec is a fixed command; HOME is expanded by the shell at launch time,
# not interpolated into a desktop entry (safe with $, backticks, quotes in HOME).
cat > "$HOME/.local/share/applications/eg-clicker.desktop" <<'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=EG-Clicker
Comment=Ehrhart Group browser audio auto-clicker
Exec=/usr/bin/python3 -c "import runpy,pathlib,sys;sys.path.insert(0,str(pathlib.Path.home() / '.local/share/eg-clicker'));runpy.run_path(str(pathlib.Path.home() / '.local/share/eg-clicker/EG-Clicker.py'),run_name='__main__')"
TryExec=/usr/bin/python3
Icon=eg-clicker
Terminal=false
Categories=Utility;Accessibility;
StartupNotify=true
EOF

systemctl --user daemon-reload
systemctl --user enable --now waytool.service || fail 'Could not start waytool user service. Check systemctl --user status waytool.service.'

echo
printf 'Installation succeeded.\nLaunching EG-Clicker…\n'
( cd "$DEST" && /usr/bin/python3 "$DEST/EG-Clicker.py" ) &
disown || true
printf 'EG-Clicker is now available in your KDE application menu.\n'
