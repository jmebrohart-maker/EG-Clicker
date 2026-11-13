"""Launch exactly the selected browser, with an argument list and no shell."""
import os
import subprocess
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

def trusted_linux_executable(name):
    # Never select a program from CWD, user PATH, or writable system binaries.
    for directory in ('/usr/bin', '/bin'):
        path = Path(directory) / name
        try:
            info = path.stat()
            if path.is_file() and os.access(path, os.X_OK) and info.st_uid == 0 and not info.st_mode & 0o022:
                return str(path)
        except OSError:
            continue
    return None


def browser_executable(browser):
    if browser not in COMMANDS:
        raise ValueError('Choose a supported browser.')
    if os.name != 'nt':
        for command in COMMANDS[browser]:
            path = trusted_linux_executable(command)
            if path:
                return path
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
        if os.name == 'nt':
            os.startfile(url)
            return
        executable = trusted_linux_executable('xdg-open')
        if not executable:
            raise RuntimeError('Trusted /usr/bin/xdg-open was not found.')
    else:
        executable = browser_executable(browser)
    environment = dict(os.environ)
    if os.name != 'nt':
        environment['PATH'] = '/usr/bin:/bin'
    process = subprocess.Popen([executable, url], env=environment,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        code = process.wait(timeout=0.3)
        if code:
            raise RuntimeError(f'{browser} exited with code {code}.')
    except subprocess.TimeoutExpired:
        pass
