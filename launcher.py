"""Launch exactly the selected browser, with an argument list and no shell."""
import os
import shutil
import subprocess
import webbrowser
from pathlib import Path

COMMANDS = {
    'Firefox': ('firefox',), 'Chrome': ('google-chrome', 'google-chrome-stable'),
    'Edge': ('microsoft-edge', 'microsoft-edge-stable'),
    'Chromium': ('chromium', 'chromium-browser'),
    'Brave': ('brave-browser', 'brave'), 'Opera': ('opera',),
    'Vivaldi': ('vivaldi', 'vivaldi-stable'),
}
WINDOWS_PATHS = {
    'Firefox': 'Mozilla Firefox/firefox.exe', 'Chrome': 'Google/Chrome/Application/chrome.exe',
    'Edge': 'Microsoft/Edge/Application/msedge.exe', 'Brave': 'BraveSoftware/Brave-Browser/Application/brave.exe',
    'Chromium': 'Chromium/Application/chrome.exe', 'Opera': 'Programs/Opera/launcher.exe',
    'Vivaldi': 'Vivaldi/Application/vivaldi.exe',
}

def browser_executable(browser):
    if browser not in COMMANDS:
        raise ValueError('Choose a supported browser.')
    for command in COMMANDS[browser]:
        found = shutil.which(command)
        if found:
            return found
    if os.name == 'nt':
        for variable in ('PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA'):
            base = os.environ.get(variable)
            if base:
                path = Path(base) / WINDOWS_PATHS[browser]
                if path.is_file():
                    return str(path)
    raise RuntimeError(f'{browser} was not found. Install it or select another browser.')

def launch_browser(browser, url):
    from urllib.parse import urlsplit
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise ValueError('Only full HTTP(S) website URLs are supported.')
    if browser == 'Any Browser':
        if not webbrowser.open(url, new=2):
            raise RuntimeError('The default browser could not be opened.')
        return
    process = subprocess.Popen([browser_executable(browser), url],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        code = process.wait(timeout=0.3)
        if code:
            raise RuntimeError(f'{browser} exited with code {code}.')
    except subprocess.TimeoutExpired:
        pass
