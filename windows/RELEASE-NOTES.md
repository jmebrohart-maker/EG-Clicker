# EG-Clicker for Windows 3.1.0 — Preview

A clean Windows edition of EG-Clicker with the modern EG interface and a
self-contained, per-user installer.

## Download and run

Download **EG-Clicker-Windows-Setup-3.1.0.exe**, close any older EG-Clicker window,
and double-click Setup. It installs, creates shortcuts, registers its uninstaller
and starts the application. Python and the audio libraries are bundled.

The Portable ZIP is available for users who prefer extraction over installation.
Keep the executable and `_internal` directory together. Check download hashes
against `SHA256SUMS-Windows.txt`.

## Highlights

- Modern EG branding, Segoe UI, persistent Settings and visible Activity logs.
- Anywhere on desktop by default, with optional browser-window targeting.
- Selected-browser audio-session metering, rather than shared speaker activity.
- DPI-aware Win32 pointer/display handling and verified input placement.
- Native Apps & Features/Start-menu uninstall; settings and logs survive upgrades.
- Hash-locked build dependencies and bundled third-party license notices.

## Validation and scope

This preview is built on a Windows x64 GitHub runner. Automated checks cover
settings, UI callbacks, audio-session isolation, Win32 structure layout, guarded
input behavior, the frozen runtime, and a silent install/uninstall cycle.
Actual Windows 11 browser/audio workflows need user testing.

The installer is currently unsigned; Windows may show an unknown-publisher or
SmartScreen prompt. Obtain files from this release and verify the checksums.
No Windows security setting is disabled, and the app does not elevate to control
administrator applications or the secure desktop.

[Windows guide](https://github.com/jmebrohart-maker/EG-Clicker/blob/main/windows/README.md) ·
[Report an issue](https://github.com/jmebrohart-maker/EG-Clicker/issues/new/choose) ·
[Fedora edition](https://github.com/jmebrohart-maker/EG-Clicker/releases/tag/v3.1.0)
