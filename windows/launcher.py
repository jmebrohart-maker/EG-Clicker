"""Launch installed Windows browsers through explicit paths, never shell commands."""
import os
from pathlib import Path, PureWindowsPath
import subprocess
from urllib.parse import urlsplit

EXECUTABLES = {'Firefox':'firefox.exe', 'Chrome':'chrome.exe', 'Edge':'msedge.exe',
               'Chromium':'chromium.exe', 'Brave':'brave.exe', 'Opera':'opera.exe', 'Vivaldi':'vivaldi.exe'}
RELATIVE_PATHS = {
    'Firefox': ('Mozilla Firefox/firefox.exe', 'Programs/Mozilla Firefox/firefox.exe'),
    'Chrome': ('Google/Chrome/Application/chrome.exe',),
    'Edge': ('Microsoft/Edge/Application/msedge.exe',),
    'Chromium': ('Chromium/Application/chrome.exe',),
    'Brave': ('BraveSoftware/Brave-Browser/Application/brave.exe',),
    'Opera': ('Opera/launcher.exe','Programs/Opera/launcher.exe'),
    'Vivaldi': ('Vivaldi/Application/vivaldi.exe',),
}


def _registered_paths(executable):
    import winreg
    key = str(PureWindowsPath('Software','Microsoft','Windows','CurrentVersion','App Paths',executable))
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(hive, key, 0, winreg.KEY_READ | view) as handle:
                    value, _kind = winreg.QueryValueEx(handle, None)
                    if isinstance(value, str):yield os.path.expandvars(value).strip().strip('"')
            except OSError:
                continue


def browser_executable(browser):
    if browser not in EXECUTABLES:raise ValueError('Choose a supported browser.')
    candidates = list(_registered_paths(EXECUTABLES[browser]))
    for variable in ('PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA'):
        base = os.environ.get(variable)
        if base:
            candidates.extend(str(Path(base) / relative) for relative in RELATIVE_PATHS[browser])
    for candidate in candidates:
        path = Path(candidate)
        if path.is_absolute() and path.suffix.lower() == '.exe' and path.is_file() and not path.is_symlink():
            return str(path)
    raise RuntimeError(f'{browser} was not found. Install it or select another browser.')


def launch_browser(browser, url):
    parsed = urlsplit(url)
    if parsed.scheme not in ('http','https') or not parsed.hostname:
        raise ValueError('Enter a complete HTTP(S) website URL.')
    if browser == 'Any Browser':
        os.startfile(url)
        return
    process = subprocess.Popen([browser_executable(browser), url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        result = process.wait(timeout=0.3)
        if result:raise RuntimeError(f'{browser} exited with code {result}.')
    except subprocess.TimeoutExpired:
        pass
