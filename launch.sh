#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -x "$HERE/eg-clicker" ]]; then
  exec "$HERE/eg-clicker" "$@"
fi
exec /usr/bin/python3 "$HERE/EG-Clicker.py" "$@"
