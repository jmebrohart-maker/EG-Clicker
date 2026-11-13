# EG-Clicker 3.1.0

An audio controlled desktop clicker by **Ehrhart Group LLC**. Rust starts the
application; Python/Tk handles the interface, settings, audio and pointer control.
The interface uses standard Tk/ttk, with no extra GUI package to install.

![EG-Clicker interface](docs/interface.png)

*Interface preview with sample activity.*

## Install and run with curl

Close any older EG-Clicker window, then run this entire block as your normal user
on **Fedora 44 KDE Plasma Wayland**. Approve Fedora's package authorization when
prompted, and any waytool input/screen-sharing consent dialog.

```bash
(
  set -euo pipefail
  EG_INSTALL_DIR="$(mktemp -d)"
  trap 'rm -rf -- "$EG_INSTALL_DIR"' EXIT
  curl --fail --location --show-error --retry 3 \
    'https://github.com/jmebrohart-maker/EG-Clicker/archive/9dd4d029399668483be48ea9b00da9a0651e7e4f.tar.gz' \
    --output "$EG_INSTALL_DIR/eg-clicker.tar.gz"
  tar -xzf "$EG_INSTALL_DIR/eg-clicker.tar.gz" \
    --strip-components=1 -C "$EG_INSTALL_DIR"
  bash "$EG_INSTALL_DIR/install-fedora.sh"
)
```

The download is pinned to the 3.1.0 implementation commit. Requires `curl` and `tar`. The repository is public; no GitHub login is needed.
The installer installs Fedora dependencies, adds the app to your menu and starts
it. Confirm **3.1.0** in the app header. Rust is optional for this installation.

After installation, launch **EG-Clicker** from the menu or run:

```bash
python3 "$HOME/.local/share/eg-clicker/EG-Clicker.py"
```

From an extracted source folder with dependencies already installed:

```bash
bash launch.sh
```

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
