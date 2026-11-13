# Changelog

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
