# Changelog

## [3.1.1] — 2026-11-23

- Retry up to three fresh KWin coordinate queries for empty, malformed or failed
  reads, serializing kdotool commands from app workers. Never use cached or target
  coordinates to pass click verification.
- Add a visible Reconnect pointer action to start the static waytool service and
  wait for desktop permission without moving or clicking. Arm and Save check input
  readiness first; reconnect never arms automatically.
- Keep strict positioning checks and explain pointer recovery in the README.
- Include the prospective custom license and preserved MIT notice in installations.
  Published older releases keep their original licenses.

## Licensing introduced after 3.1.0

- Adopt the EG-Clicker Free Use / No Modifications License 1.0 for future
  distributions: free personal/noncommercial use and commercial use below 100
  employees; written permission required for commercial use at 100 or more
  employees and for modifications.
- Preserve prior MIT grants and third-party licenses. Published 3.1.0 release
  assets and tags retain their original terms.


## Windows 3.1.0 Preview — 2026-11-13

- Modern EG interface and a separate Windows project under `windows/`.
- Self-contained per-user Setup executable and portable ZIP; no system Python or WinGet required.
- Native Win32 DPI/display/input handling and selected-browser session audio metering.
- Hash-locked build dependencies, bundled license notices and native install/uninstall validation.

## [3.1.0] — 2026-11-13

### Added

- Modern EG-branded interface with a visible Activity panel and separate Settings.
- Anywhere on desktop as the default click mode, with an optional browser-window restriction.
- Persistent settings, website launch, recent log restoration, copy/export controls and visible GUI errors.
- Rust launcher, regression tests, CI checks and versioned release packaging.

### Fixed

- Shifted KScreen origins by using live Wayland monitor geometry.
- Browser capture rejecting valid Wayland app IDs as though they were process names.
- Slow Arm checks blocking the UI, and compatible browser changes discarding targets.
- Static waytool service startup and uninstall instructions that depended on the current directory.

### Security

- Restricted executable lookup and sibling-only native launcher behavior.
- Pointer verification in both click modes; optional window/process checks in browser-only mode.
- Pinned waytool checksums and signed build-provenance verification before downloaded RPM installation.

[3.1.0]: https://github.com/jmebrohart-maker/EG-Clicker/releases/tag/v3.1.0

[3.1.1]: https://github.com/jmebrohart-maker/EG-Clicker/releases/tag/v3.1.1
