#!/usr/bin/env bash
# EG-Clicker Fedora 44 KDE Wayland per-user installer
set -Eeuo pipefail
export PATH=/usr/bin:/bin
umask 077
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
fail(){ echo; echo "INSTALL FAILED: $*" >&2; echo 'Press Enter to close.'; read -r _ || true; exit 1; }
trap 'echo "Installer stopped at line $LINENO (exit code $?)." >&2' ERR

printf '\n===== EG-Clicker • Fedora 44 KDE Wayland =====\n\n'
[[ -r "$HERE/EG-Clicker.py" && -r "$HERE/eg_platform.py" && -r "$HERE/launcher.py" && -r "$HERE/window_guard.py" ]] || fail "EG-Clicker.py, eg_platform.py launcher.py and window_guard.py must be beside the installer. Extract the ZIP first."
[[ -r "$HERE/eg_logo_icon.png" ]] || fail 'Missing icon file; extract entire ZIP.'
[[ $(id -u) != 0 ]] || fail 'Run as your desktop user, not as root.'
[[ ${XDG_SESSION_TYPE:-} == wayland ]] || fail 'Log into KDE Plasma Wayland, then run this installer.'
[[ -e /etc/fedora-release ]] || fail 'This installer is for Fedora Linux.'
FEDORA_VER="$(rpm -E '%fedora')"
[[ $FEDORA_VER == 44 ]] || fail "Expected Fedora 44, found Fedora $FEDORA_VER."
for binary in dnf curl python3; do command -v "$binary" >/dev/null || fail "Missing system command $binary"; done
command -v pkexec >/dev/null || fail 'polkit pkexec not found. Install polkit or use an admin account.'

PKGS=(python3 python3-tkinter pulseaudio-utils kdotool libkscreen xdg-desktop-portal-kde curl gh)
# Only Fedora repository dependencies are installed before artifact verification.
printf 'Dependency installation requires a Fedora administrator authorization dialog.\n'
pkexec /usr/bin/dnf install -y "${PKGS[@]}" || fail 'Fedora dependency installation was denied or failed.'

WAYTOOL_VERSION='v1.0.1'
WAYTOOL_SOURCE='007baab54cc9142d27c353790976cefcf62224e6'
TMPDIR_EG="$(mktemp -d)"
trap 'rm -rf -- "$TMPDIR_EG"' EXIT
if [[ ! -x /usr/bin/waytool ]]; then
  ARCH="$(uname -m)"
  # Release bytes pinned in this source, not fetched from release metadata.
  case "$ARCH" in
    x86_64) EXPECTED_SHA='d8158b07c2f7aa18f1592668e07c189ffb9e20f78b648519a93a58c26e29658b' ;;
    aarch64) EXPECTED_SHA='e1b97b70e10cb6c9d01865f16a7299a598c84e117fd6adcbcf3f18d9f70324e9' ;;
    *) fail "Unsupported architecture $ARCH" ;;
  esac
  BUNDLE="$HERE/provenance/waytool-1.0.1-$ARCH.sigstore.json"
  [[ -r "$BUNDLE" ]] || fail 'Missing bundled build attestation; extract the complete download.'
  RPM_FILE="$TMPDIR_EG/waytool-1.0.1-1.fc44.$ARCH.rpm"
  curl --proto '=https' --proto-redir '=https' -fL --retry 3 \
    --connect-timeout 15 --max-time 240 \
    "https://github.com/mx-shift/waytool/releases/download/$WAYTOOL_VERSION/waytool-1.0.1-1.fc44.$ARCH.rpm" \
    -o "$RPM_FILE" || fail 'waytool download failed.'
  printf '%s  %s\n' "$EXPECTED_SHA" "$RPM_FILE" | /usr/bin/sha256sum --check --status || fail 'RPM checksum mismatch. Aborting.'
  # A bundled Sigstore attestation permits verification without GitHub login.
  # Verification still refreshes Sigstore trust metadata over HTTPS. Never bypass it.
  /usr/bin/gh attestation verify "$RPM_FILE" --bundle "$BUNDLE" \
    --repo mx-shift/waytool \
    --cert-identity 'https://github.com/mx-shift/waytool/.github/workflows/ci.yml@refs/tags/v1.0.1' \
    --source-digest "$WAYTOOL_SOURCE" --deny-self-hosted-runners \
    || fail 'waytool build attestation rejected or verification unavailable. No RPM installed.'
  printf 'Pinned checksum and signed waytool build provenance verified.\n'
  pkexec /usr/bin/dnf install -y "$RPM_FILE" || fail 'Verified waytool RPM installation was denied or failed.'
fi
[[ -x /usr/bin/waytool ]] || fail 'waytool not found after dependency installation.'

DEST="$HOME/.local/share/eg-clicker"
mkdir -p "$DEST" "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/96x96/apps"
install -m 0644 "$HERE/EG-Clicker.py" "$DEST/EG-Clicker.py"
install -m 0644 "$HERE/launcher.py" "$DEST/launcher.py"
install -m 0644 "$HERE/window_guard.py" "$DEST/window_guard.py"
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
