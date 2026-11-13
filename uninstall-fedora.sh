#!/usr/bin/env bash
# Remove EG-Clicker-owned files and local data, never shared dependencies.
set -Eeuo pipefail
[[ $(id -u) != 0 ]] || { echo 'Run as your regular desktop user, not root.' >&2; exit 1; }
echo 'This removes EG-Clicker, saved targets, logs, shortcuts, and settings.'
echo 'System Python, system RPM dependencies and shared waytool are preserved.'
read -r -p 'Type REMOVE to continue: ' choice
[[ "$choice" == REMOVE ]] || { echo 'Cancelled.'; exit 0; }
# Scope paths to known EG-Clicker-owned leaves under user home.
remove_tree(){
  local path="$1" parent
  parent="$(dirname -- "$path")"
  if [[ -L "$parent" || -L "$path" ]]; then
    echo "Refusing symbolic-link path $path; remove manually" >&2; return 1
  fi
  [[ ! -e "$path" ]] || /usr/bin/rm -rf -- "$path"
}
/usr/bin/rm -f -- "$HOME/.local/share/applications/eg-clicker.desktop" \
  "$HOME/.local/share/icons/hicolor/96x96/apps/eg-clicker.png"
remove_tree "$HOME/.local/share/eg-clicker"
remove_tree "$HOME/.config/eg-clicker"
remove_tree "${XDG_STATE_HOME:-$HOME/.local/state}/eg-clicker"
# Leave older 'razer-audio-clicker.json' untouched: it predated EG-Clicker.
if command -v update-desktop-database >/dev/null; then
  update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
fi
printf 'EG-Clicker files, settings and logs removed. Shared packages left installed.\n'
