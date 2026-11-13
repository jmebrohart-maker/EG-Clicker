# Security policy

The current 3.1.x release is the maintained line. Security fixes are handled on a
best-effort basis; this project does not promise a response or remediation SLA.

## Reporting

Do not post credentials or sensitive exploit details in a public issue. Use the
maintainer contact options at [Ehrhart Group](https://ehrhartgroup.us) to arrange
private disclosure. General, non-sensitive hardening suggestions can be reported
through a GitHub issue.

## Security boundaries

- Run the app as your desktop user. The Fedora installer requests administrator
  authorization only for package installation.
- Anywhere mode intentionally sends input to any application at the saved point.
  Enable the optional browser-window restriction when that scope is appropriate.
- Both modes verify pointer placement. Browser-only mode also checks the saved
  window/process, focus and geometry. A window check and input command are
  separate OS operations, so this is not an atomic input-security boundary.
- Downloaded waytool RPMs require pinned SHA-256 digests and signed build
  provenance. These checks establish artifact origin/integrity, not an audit
  of the upstream program or its RPM scripts.
- Keep access to your desktop account and configuration directory private. The
  application does not isolate itself from other software running as you.

No third-party security audit or certification is claimed. Supported-platform
and validation details are recorded in the README and release notes.
