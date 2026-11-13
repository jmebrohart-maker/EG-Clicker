<p align="center">
  <img src="eg_logo_icon.png" width="88" alt="Ehrhart Group logo">
</p>
<h1 align="center">EG-Clicker</h1>
<p align="center"><strong>Audio-triggered desktop automation, with a modern EG-branded interface.</strong></p>
<p align="center">Built by Ehrhart Group LLC · Python desktop app + Rust launcher</p>
<p align="center">
  <a href="https://github.com/jmebrohart-maker/EG-Clicker/releases/tag/v3.1.0"><img src="https://img.shields.io/badge/release-v3.1.0-438dff?style=flat-square" alt="Release v3.1.0"></a>
  <a href="https://github.com/jmebrohart-maker/EG-Clicker/actions/workflows/ci.yml"><img src="https://github.com/jmebrohart-maker/EG-Clicker/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-65deb0?style=flat-square" alt="MIT license"></a>
  <img src="https://img.shields.io/badge/Fedora-44%20%7C%20KDE%20Wayland-95a9c5?style=flat-square" alt="Fedora 44 KDE Wayland">
</p>
<p align="center">
  <a href="https://github.com/jmebrohart-maker/EG-Clicker/releases/latest"><strong>Download</strong></a> ·
  <a href="#install-and-run">Install</a> ·
  <a href="CHANGELOG.md">Changelog</a> ·
  <a href="https://github.com/jmebrohart-maker/EG-Clicker/issues/new/choose">Report an issue</a>
</p>

![EG-Clicker interface](docs/interface.png)

*Interface preview with sample activity. Version 3.1.0.*

EG-Clicker monitors your selected browser. When its audio stops for two seconds,
it clicks a saved desktop location. **Anywhere on desktop** is the default;
optional browser-window targeting is available in Settings.

- Save a point, arm the clicker, and continue using your desktop.
- Tune movement retries, tolerance and settling delay.
- Keep activity visible and copy or export full diagnostic logs.
- Retain settings and recent log history between sessions.

## Install and run

**Supported target: Fedora 44, KDE Plasma Wayland.** The installer sets up
Python/Tkinter and desktop dependencies, adds EG-Clicker to your menu and starts
it. No Rust compiler or GitHub login is required.

Close any older EG-Clicker window. Run the entire block below as your normal
desktop user, and approve Fedora's package authorization when prompted:

```bash
(
  set -euo pipefail
  EG_VERSION="3.1.0"
  EG_RELEASE="https://github.com/jmebrohart-maker/EG-Clicker/releases/download/v${EG_VERSION}"
  EG_INSTALL_DIR="$(mktemp -d)"
  trap 'rm -rf -- "$EG_INSTALL_DIR"' EXIT
  curl --fail --location --show-error --retry 3 \
    "$EG_RELEASE/EG-Clicker-v${EG_VERSION}.tar.gz" \
    --output "$EG_INSTALL_DIR/EG-Clicker-v${EG_VERSION}.tar.gz"
  curl --fail --location --show-error --retry 3 \
    "$EG_RELEASE/SHA256SUMS" --output "$EG_INSTALL_DIR/SHA256SUMS"
  (cd "$EG_INSTALL_DIR" && sha256sum --check --ignore-missing SHA256SUMS)
  tar -xzf "$EG_INSTALL_DIR/EG-Clicker-v${EG_VERSION}.tar.gz" \
    --strip-components=1 -C "$EG_INSTALL_DIR"
  bash "$EG_INSTALL_DIR/install-fedora.sh"
)
```

Requires `curl`, `tar` and `sha256sum` (standard Fedora utilities). Accept any
waytool input/screen-sharing consent dialog. Each release provides tar.gz/ZIP
install bundles and `SHA256SUMS`; these bundles contain the application source
and installer, not a standalone compiled GUI executable.

After installing, open **EG-Clicker** from the application menu or run:

```bash
python3 "$HOME/.local/share/eg-clicker/EG-Clicker.py"
```

From an extracted bundle with dependencies already installed, use
`bash launch.sh`. The release is public, and the app uses standard Tk/ttk
without an additional GUI framework.

## Click anywhere, or restrict it in Settings

**Anywhere on desktop is the default.** The selected browser is the audio source,
not a requirement for where the click lands. You can capture any location on an
active display and use other applications while that browser's audio is monitored.
When audio stops for two seconds, the saved location receives the click, including
whatever application is at that point.

1. Select the browser to monitor. Optionally enter a website and press **Launch**.
2. Press **Save Next · 4s**, then place your pointer at the desired click location.
3. Press **Arm clicker**. **Disarm clicker** pauses automation.

For browser-only behavior, open **Settings**, check **Require the captured browser
window**, and press **Save settings**. Capture the target again on that browser.
This optional mode requires the same browser window to remain active, uncovered,
and at the same position/size. It disarms on a mismatch. Leave the option unchecked
for unrestricted desktop coordinates. The main control panel shows the saved mode.

![Clicker settings](docs/settings.png)

Settings also control retries, tolerance and settling delay. **Save settings**
persists changes and pauses monitoring. **Restore defaults** saves Anywhere mode,
retries disabled, 4px tolerance, and 200ms settling delay. Browser selection, launch
URL and target are preserved in `~/.config/eg-clicker/config.json` on Linux.

Pointer position is verified in both modes. Monitor changes require recapturing
the target. Live waytool monitor coordinates are used instead of a potentially
shifted KScreen configuration origin. Browser-only mode verifies the protected
process and captured window identity; a Wayland app ID is not treated as a process
name. The window check and input command are separate OS operations.

## Activity and logs

**Activity stays visible beside the controls**, including on smaller windows.
It shows compact times and colored errors; **Copy** and **Export** retain full
original entries. **Open Logs** opens a larger, independent log window.

Recent entries are restored on restart (up to 300 lines, with bounded reads).
Disk logs remain at `~/.local/state/eg-clicker/eg-clicker.log`, or under your
`XDG_STATE_HOME` if set. Oversized logs rotate to `eg-clicker.previous.log` at
startup. GUI callback errors stop automation and open copyable diagnostics.

Optional **Pointer tests** offer Move only, Test click, and Check setup.

## Dependencies and service

Linux needs Python 3/Tkinter, `pactl`, `kdotool`, `kscreen-doctor`, and waytool.
The installer currently targets Fedora **44**; Fedora 45 is not validated.

waytool's upstream unit is static: start it rather than enabling it.

```bash
systemctl --user start waytool.service
systemctl --user is-active waytool.service
```

The second command should report `active`. An older installer's “no installation
config” warning did not mean app-file installation failed.

Downloaded waytool 1.0.1 RPMs must match source-pinned checksums and bundled
Sigstore attestations verified by Fedora's `gh` package. Repository, workflow,
source commit and hosted runner identity are enforced before privileged RPM
installation. Verification needs HTTPS access to trust metadata, but no login.
Existing system-installed waytool is reused. See [provenance details](provenance/README.md).

## Build and verify

```bash
cargo build --release
cp target/release/eg-clicker ./eg-clicker
bash launch.sh
```

Keep the executable beside all Python modules, including `eg_ui.py`. Rust only
loads its regular sibling `EG-Clicker.py`. `EG_CLICKER_PYTHON` can specify an
absolute interpreter path. No executable is committed.

```bash
python3 -m unittest discover -s tests -v
cargo test
python3 EG-Clicker.py --diagnose
```

Real Tk GUI tests run when `DISPLAY` is available (for example under Xvfb).
Tests cover both click modes, persisted settings/logs, GUI controls, and coordinate
and input checks with simulated desktop integration. Live Fedora behavior still
requires desktop testing. Optional browser-window verification requires KDE
Wayland. The inherited Windows backend is unvalidated for this update.

## Uninstall

Close EG-Clicker, then run from **any terminal directory**:

```bash
bash "$HOME/.local/share/eg-clicker/uninstall-fedora.sh"
```

Type `REMOVE`. This removes the app, saved targets, settings and logs. Shared
system packages and waytool remain. The short command `bash uninstall-fedora.sh`
only works from the extracted source folder; curl's staging folder is deleted
after installation.

Licensed under the [MIT License](LICENSE).

## Project information

- [Release notes and downloads](https://github.com/jmebrohart-maker/EG-Clicker/releases)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Release checklist](docs/RELEASING.md)

Issues and focused pull requests are welcome. Please include your app version,
desktop environment and relevant logs when reporting a problem.
