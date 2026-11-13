EG-Clicker 2.3.3 - Simple Controls / Hardened Fedora 44 KDE Wayland Edition

Extract this ZIP completely. Double-click "Install EG-Clicker.desktop" or run
  bash install-fedora.sh
from the extracted directory. Approve the Fedora package authorization dialog.

Installs Python/Tk/Pulse tooling from Fedora's configured repos and waytool
v1.0.1 from its exact pinned GitHub release ONLY when /usr/bin/waytool is absent.
The RPM is installed only when GitHub release metadata has a valid SHA-256
digest and the downloaded bytes match. Missing hashes fail closed. Note that
release metadata is still remote: this is not an independently baked-in hash
or an audit of upstream RPM scripts. Use a fully audited hash+signature policy
for high-assurance enterprise deployment.

Run: open "EG-Clicker" from the KDE app menu.
Uninstall: run ~/.local/share/eg-clicker/uninstall-fedora.sh or the script
included in this ZIP. Type REMOVE to remove EG-Clicker app/config/logs/icons.
Shared Fedora packages and waytool stay installed and active because they may
belong to other applications. Terminal logs, downloads, backups, and system
package-manager history are not scrubbed.

The installer does not run the GUI as root. Browser audio detection varies by
browser and sink activity. Movement tests are OPTIONAL. To use: Save Next (4s), choose browser, then Arm / Disarm.
For Move Only, Test Click, Check Displays, and diagnostic logs, expand
Testing & Troubleshooting. The app always checks actual pointer placement
before a click and cancels when coordinates do not match.
