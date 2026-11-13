# EG-Clicker 3.0.1

Browser audio controlled clicker for Fedora 44 KDE Plasma Wayland, with a
Rust launcher and Python/Tkinter desktop application.

## Install and run with curl

Run this entire block in a terminal on **Fedora 44 KDE Plasma Wayland**, as your
normal desktop user. It downloads the complete 3.0.1 source, installs dependencies
through the Fedora authorization dialog, installs EG-Clicker, and launches it:

```bash
(
  set -euo pipefail
  EG_INSTALL_DIR="$(mktemp -d)"
  trap 'rm -rf -- "$EG_INSTALL_DIR"' EXIT
  curl --fail --location --show-error --retry 3 \
    'https://github.com/jmebrohart-maker/EG-Clicker/archive/b269fd1b4079b6fb6853991e6bbdf47404d7875e.tar.gz' \
    --output "$EG_INSTALL_DIR/eg-clicker.tar.gz"
  tar -xzf "$EG_INSTALL_DIR/eg-clicker.tar.gz" \
    --strip-components=1 -C "$EG_INSTALL_DIR"
  bash "$EG_INSTALL_DIR/install-fedora.sh"
)
```

Requires `curl` and `tar`. The download is pinned to the 3.0.1 security-fix implementation
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
browser, URL, target/display layout, captured window identity, retries, tolerance
and settle delay.
Defaults: retries disabled, one extra retry when enabled, 4px tolerance,
200ms settle delay. Pointer mismatches cancel the click and disarm the app.
Monitor arrangement changes require capturing the target again.

### Testing the security fixes

After upgrading, **capture the target again with Save Next**. Old targets have
no window identity and cannot be armed. Keep the selected browser active and
uncovered. Closing/reopening, moving, or resizing it requires another capture.
The supported click backend in this hardened release is Fedora 44 KDE Wayland
with a native, protected system browser installation. Flatpak/portable browser
identity may not be verifiable; in that case the app refuses to click.

1. Launch the browser and capture Next. Optionally use Move Only first.
2. Start browser audio, arm the app, and let playback stop. With the browser
   active and unchanged, the normal delayed click should work.
3. Repeat, but switch to another app or cover the target before audio stops.
   The click must be cancelled and the clicker must disarm.
4. Move/resize or close the browser and repeat. The click must be cancelled;
   capture again before resuming.

Window identity, process identity, geometry, focus, and the topmost window at
the pointer are checked immediately before input. These checks reduce wrong
window clicks, but a desktop change can still race the separate input command;
this is not an atomic OS-level guarantee.

## Build the Rust launcher

This is a hybrid application: Rust locates and starts the Python GUI, forwards
arguments, and returns its exit status. Python handles settings, browser launch,
audio monitoring and pointer integration. No compiled binary is tracked here.

```bash
cargo build --release
cp target/release/eg-clicker ./eg-clicker
bash launch.sh
```

Keep the executable beside `EG-Clicker.py`, `eg_platform.py`, `launcher.py`, and `window_guard.py`
when distributing it. `launch.sh` uses this executable when present and Python
otherwise. `EG_CLICKER_PYTHON` selects an absolute Python interpreter path for Rust.
The Fedora installer installs the Python application and does not require Rust.

The inherited Windows backend is retained, but secure window verification is
currently implemented only for KDE Wayland. This version deliberately refuses
capture/click actions on Windows. The GUI and settings remain usable there.

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

The installer pins waytool v1.0.1 RPM SHA-256 digests directly in the source.
Before installing a downloaded RPM, it also verifies the bundled Sigstore build
attestation with Fedora's `gh` package, requiring the publisher repository,
release workflow identity, exact source commit, and a GitHub-hosted runner.
A checksum or attestation failure stops the RPM installation. No GitHub login
is required; HTTPS access to Sigstore trust metadata is required. Existing
system-installed waytool is reused.

Only Fedora repository dependencies are installed before verification. Signed
build provenance establishes origin and integrity, not an audit of upstream RPM
scripts. See [provenance details](provenance/README.md).

The launcher loads only its sibling Python app and rejects script symlinks.
Browser launch uses protected system paths instead of user PATH entries.

Close EG-Clicker, then uninstall from any terminal directory with:

```bash
bash "$HOME/.local/share/eg-clicker/uninstall-fedora.sh"
```

Type `REMOVE` when prompted. This removes EG-Clicker files, settings and logs.
Shared system packages and waytool remain installed. `bash uninstall-fedora.sh`
only works when your terminal is inside the extracted source folder; curl's
installation staging folder is automatically deleted after installation.

Licensed under the [MIT License](LICENSE).
