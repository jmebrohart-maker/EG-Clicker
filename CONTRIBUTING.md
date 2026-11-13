# Contributing to EG-Clicker

Bug reports, documentation fixes and focused improvements are welcome.
For a larger change, open an issue describing the workflow before implementing it.

## Development

Use Python 3.11 or newer with Tkinter, and current stable Rust for launcher work.
The supported desktop is Fedora 44 KDE Plasma Wayland. Keep development tools in
a virtual environment; do not run the GUI or development commands as root.

```bash
python3 EG-Clicker.py
python3 -m unittest discover -s tests -v
cargo test --locked
shellcheck install-fedora.sh uninstall-fedora.sh launch.sh
python3 scripts/verify_manifest.py
```

On headless Linux, use `xvfb-run -a python3 -m unittest discover -s tests -v` to
include real Tk callback tests. They simulate desktop input and do not establish
live Wayland behavior. Installer dependency installation is separate from tests.

## Changes and pull requests

Keep changes focused. Explain the user-visible behavior and how you checked it.
Add a regression test for behavior changes. For pointer changes, retain live
position verification and test both Anywhere and browser-only modes. Never add
a fallback that clicks after failed verification in the restricted mode.

Preserve the EG logo, company attribution, license and accessible color contrast.
Avoid new runtime dependencies unless the benefit and installation path are clear.
Do not commit generated binaries, credentials, user configs or diagnostic logs.

If tracked files change, refresh `SHA256-MANIFEST.json` with SHA-256 digests for
all tracked files except the manifest itself. The manifest check must pass.

## Reporting security problems

Read [SECURITY.md](SECURITY.md) before posting sensitive details.

## Releases

See [the release checklist](docs/RELEASING.md). Contributions are provided under
the repository's [MIT license](LICENSE).
