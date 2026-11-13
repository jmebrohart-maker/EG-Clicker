# EG-Clicker 3.0

Browser audio controlled clicker for Fedora 44 KDE Plasma Wayland, with a
Rust launcher and Python/Tkinter desktop application.

## Install and run with curl

Run this entire block in a terminal on **Fedora 44 KDE Plasma Wayland**, as your
normal desktop user. It downloads the complete 3.0 source, installs dependencies
through the Fedora authorization dialog, installs EG-Clicker, and launches it:

```bash
(
  set -euo pipefail
  EG_INSTALL_DIR="$(mktemp -d)"
  trap 'rm -rf -- "$EG_INSTALL_DIR"' EXIT
  curl --fail --location --show-error --retry 3 \
    'https://github.com/jmebrohart-maker/EG-Clicker/archive/054a63f8e8087c18065922637b928861e96b0816.tar.gz' \
    --output "$EG_INSTALL_DIR/eg-clicker.tar.gz"
  tar -xzf "$EG_INSTALL_DIR/eg-clicker.tar.gz" \
    --strip-components=1 -C "$EG_INSTALL_DIR"
  bash "$EG_INSTALL_DIR/install-fedora.sh"
)
```

Requires `curl` and `tar`. The download is pinned to the 3.0 implementation
commit from [PR #1](https://github.com/jmebrohart-maker/EG-Clicker/pull/1).
The repository must be **public** for this command to download without a token.
Do not run the block with `sudo`; the installer requests authorization when needed.
Rust is optional and is not required for this installation.

After installation, open **EG-Clicker** from the application menu, or run:

```bash
python3 "$HOME/.local/share/eg-clicker/EG-Clicker.py"
```

## Start from an extracted download

Extract or clone the whole repository. On Fedora 44 KDE Wayland, run:

```bash
bash install-fedora.sh
```

The installer requests administrator authorization for Fedora dependencies,
installs the application for the current user, and adds **EG-Clicker** to the
application menu. It does not run the GUI as root.

With dependencies already installed:

```bash
bash launch.sh
# Or start Python directly:
python3 EG-Clicker.py
```

Required Linux dependencies are Python 3, Tkinter, `pactl`, `kdotool`,
`kscreen-doctor`, and `waytool` with its user service running. The installer
currently targets Fedora **44**. Fedora 45 is not validated.

## Launch, settings, and automation

1. Choose your browser, enter a complete `https://` or `http://` website URL,
   and press **Launch Browser**. The URL is saved for the next session.
   The selected browser must be installed; **Any Browser** uses your default.
2. Press **Save Next (4s)** and move the pointer onto the website's Next button
   before capture. The app minimizes while capturing the position.
3. Expand **Pointer Reliability Settings**, choose your values, and press
   **Save Settings**. **Restore Safe Defaults** also saves the defaults.
4. Press **Arm / Disarm** to begin monitoring. After detected browser audio
   stops for two seconds, the app verifies the saved pointer position and
   sends a click. Press it again to stop.

**Launch Browser** opens the website. **Arm / Disarm** controls automatic
clicking. Saving settings or changing browsers disarms automation; re-arm
when ready. Optional pointer tests and diagnostic logs are under
**Testing & Troubleshooting**.

Settings persist in `~/.config/eg-clicker/config.json` on Linux, including the
browser, URL, target/display layout, retries, tolerance and settle delay.
Defaults: retries disabled, one extra retry when enabled, 4px tolerance,
200ms settle delay. Pointer mismatches cancel the click and disarm the app.
Monitor arrangement changes require capturing the target again.

## Build the Rust launcher

This is a hybrid application: Rust locates and starts the Python GUI, forwards
arguments, and returns its exit status. Python handles settings, browser launch,
audio monitoring and pointer integration. No compiled binary is tracked here.

```bash
cargo build --release
cp target/release/eg-clicker ./eg-clicker
bash launch.sh
```

Keep the executable beside `EG-Clicker.py`, `eg_platform.py`, and `launcher.py`
when distributing it. `launch.sh` uses this executable when present and Python
otherwise. `EG_CLICKER_PYTHON` selects a specific Python interpreter for Rust.
The Fedora installer installs the Python application and does not require Rust.

The inherited Windows backend remains available using Python with Tkinter,
`pycaw` and `comtypes`, but Windows has not been validated for this update.

## Verification and diagnostics

```bash
python3 -m unittest discover -s tests -v
cargo test
python3 EG-Clicker.py --diagnose
```

Automated checks cover config recovery and persistence, browser launch arguments,
settings callbacks, and pointer verification with mocked desktop commands.
They do not establish live Fedora Wayland pointer/audio behavior or browser
navigation. Browser audio detection depends on the browser's audio sessions.

## Installer and removal

The installer retains the pinned waytool v1.0.1 RPM download. It requires an
upstream SHA-256 digest in GitHub release metadata and checks the downloaded
bytes. This is not an independently pinned checksum or an audit of RPM scripts.

Run `bash uninstall-fedora.sh` to remove EG-Clicker files, settings and logs;
type `REMOVE` when prompted. Shared system packages and waytool remain installed.

Licensed under the [MIT License](LICENSE).
