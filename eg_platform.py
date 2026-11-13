"""EG-Clicker platform integration for Fedora KDE Wayland and Windows 11.

Linux uses the existing known-good KScreen/kdotool/waytool implementation.
Windows uses Win32 cursor coordinates and Core Audio sessions via pycaw.
"""
from __future__ import annotations
import ctypes
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import threading

IS_WINDOWS = os.name == 'nt'
BROWSERS = ('Firefox', 'Chrome', 'Edge', 'Chromium', 'Brave', 'Opera', 'Vivaldi', 'Any Browser')
CONFIG = (Path(os.environ.get('APPDATA', str(Path.home()))) / 'EG-Clicker' / 'config.json') if IS_WINDOWS else (Path.home() / '.config' / 'eg-clicker' / 'config.json')
LEGACY_CONFIG = Path.home() / '.config' / 'razer-audio-clicker.json' if not IS_WINDOWS else Path.home() / '.eg-clicker-legacy-unused'
LOG_FILE = (Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'EG-Clicker' / 'logs' / 'eg-clicker.log') if IS_WINDOWS else (Path(os.environ.get('XDG_STATE_HOME', str(Path.home() / '.local' / 'state'))) / 'eg-clicker' / 'eg-clicker.log')

LINUX_NAMES = {
    'Firefox': ('firefox',),
    'Chrome': ('google-chrome', 'chrome', 'chromium-browser'),
    'Edge': ('microsoft-edge', 'edge'),
    'Chromium': ('chromium',),
    'Brave': ('brave',),
    'Opera': ('opera',),
    'Vivaldi': ('vivaldi',),
}
WINDOWS_NAMES = {
    'Firefox': ('firefox.exe',), 'Chrome': ('chrome.exe',),
    'Edge': ('msedge.exe',), 'Chromium': ('chromium.exe',),
    'Brave': ('brave.exe',), 'Opera': ('opera.exe',),
    'Vivaldi': ('vivaldi.exe',),
}

def _matches(name: str, browser: str, platform: str):
    name = name.lower()
    choices = WINDOWS_NAMES if platform == 'windows' else LINUX_NAMES
    if browser == 'Any Browser':
        tokens = tuple(t for values in choices.values() for t in values)
    else:
        tokens = choices.get(browser, ())
    if platform == 'windows':
        return name in tokens
    # Match process binary or application name without matching arbitrary website titles.
    return any(name == t or name.startswith(t + '-') or name.startswith(t + '.') for t in tokens)

def display_point(point):
    return f'({point[0]}, {point[1]})'

def run_cmd(*args, timeout=12, trace=None, quiet=False):
    # Fedora: never run a same-named executable from a writable PATH directory.
    if not IS_WINDOWS:
        executable = next((str(Path(directory) / args[0]) for directory in ('/usr/bin', '/bin')
                           if (Path(directory) / args[0]).is_file() and os.access(Path(directory) / args[0], os.X_OK)), None)
        if executable is None:
            raise RuntimeError(f'Missing trusted system command: {args[0]}')
        args = (executable, *args[1:])
    elif not shutil.which(args[0]):
        raise RuntimeError(f'Missing command: {args[0]}')
    if trace and not quiet:
        trace('COMMAND', 'argv=' + ' '.join(map(str, args)))
    start = time.monotonic()
    try:
        res = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise RuntimeError(f'{args[0]} failed: {exc}') from exc
    if trace and not quiet:
        trace('COMMAND', f'exit={res.returncode} elapsed={time.monotonic()-start:.3f}s stdout={res.stdout.strip()[:300]!r} stderr={res.stderr.strip()[:300]!r}')
    if res.returncode:
        raise RuntimeError(f'{args[0]} failed ({res.returncode}): {(res.stderr or res.stdout).strip()[:400]}')
    return res.stdout

def parse_screens_json(text):
    root = json.loads(text)
    if not isinstance(root, dict) or not isinstance(root.get('outputs'), list):
        raise ValueError('Unexpected kscreen-doctor JSON format')
    found = []
    for item in root['outputs']:
        if item.get('enabled') is not True or item.get('connected') is False:
            continue
        pos, size = item.get('pos'), item.get('size')
        if not isinstance(pos, dict) or not isinstance(size, dict):
            continue
        try:
            d = dict(name=str(item.get('name', '?')), x=int(pos['x']), y=int(pos['y']), w=int(size['width']), h=int(size['height']))
        except (ValueError, TypeError, KeyError):
            continue
        if d['w'] > 0 and d['h'] > 0:
            found.append(d)
    return sorted(found, key=lambda d:(d['x'],d['y'],d['name']))

def parse_screens_text(text):
    clean = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', text)
    clean = re.sub(r'\x1b\][^\x07]*(?:\x07|\x1b\\)', '', clean)
    monitors = []
    for block in re.split(r'(?=^\s*Output:\s*\d+\s+)', clean, flags=re.M):
        title = re.search(r'^\s*Output:\s*\d+\s+(\S+)', block, flags=re.M)
        if not title or not re.search(r'^\s*enabled\s*$',block, flags=re.M):
            continue
        geo = re.search(r'\bGeometry:\s*(-?\d+),\s*(-?\d+)\s+(\d+)x(\d+)', block)
        if geo:
            x,y,w,h = map(int,geo.groups())
            if w > 0 and h > 0:
                monitors.append(dict(name=title.group(1),x=x,y=y,w=w,h=h))
    return sorted(monitors,key=lambda d:(d['x'],d['y'],d['name']))

def _linux_screens():
    errors=[]
    try:
        result = parse_screens_json(run_cmd('kscreen-doctor','-j'))
        if result:
            return result
        errors.append('empty JSON')
    except (ValueError, RuntimeError) as exc:
        errors.append(str(exc))
    try:
        result = parse_screens_text(run_cmd('kscreen-doctor','-o'))
        if result:
            return result
    except RuntimeError as exc:
        errors.append(str(exc))
    raise RuntimeError('No enabled KDE monitors: '+' / '.join(errors))

def _windows_api():
    return ctypes.WinDLL(str(Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32' / 'user32.dll'), use_last_error=True)

def _windows_screens():
    from ctypes import wintypes
    user32 = _windows_api()
    class RECT(ctypes.Structure):
        _fields_ = [('left',wintypes.LONG),('top',wintypes.LONG),('right',wintypes.LONG),('bottom',wintypes.LONG)]
    class MONITORINFOEXW(ctypes.Structure):
        _fields_ = [('cbSize',wintypes.DWORD),('rcMonitor',RECT),('rcWork',RECT),('dwFlags',wintypes.DWORD),('szDevice',wintypes.WCHAR*32)]
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(RECT), wintypes.LPARAM)
    user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFOEXW)]
    user32.GetMonitorInfoW.restype = wintypes.BOOL
    user32.EnumDisplayMonitors.argtypes = [wintypes.HDC, ctypes.POINTER(RECT), callback_type, wintypes.LPARAM]
    user32.EnumDisplayMonitors.restype = wintypes.BOOL
    monitors=[]
    @callback_type
    def callback(handle, hdc, rectptr, data):
        info=MONITORINFOEXW(); info.cbSize=ctypes.sizeof(info)
        if user32.GetMonitorInfoW(handle, ctypes.byref(info)):
            r=info.rcMonitor
            monitors.append(dict(name=str(info.szDevice),x=r.left,y=r.top,w=r.right-r.left,h=r.bottom-r.top))
        return True
    if not user32.EnumDisplayMonitors(None,None,callback,0) or not monitors:
        raise RuntimeError('Windows EnumDisplayMonitors failed')
    return sorted(monitors,key=lambda d:(d['x'],d['y'],d['name']))

def init_desktop():
    if IS_WINDOWS:
        # Set before Tk creates its window. Pixel coordinates must use one DPI space.
        try:
            ctypes.WinDLL(str(Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32' / 'shcore.dll'), use_last_error=True).SetProcessDpiAwareness(2)
        except (OSError, AttributeError):
            try:
                _windows_api().SetProcessDPIAware()
            except (OSError, AttributeError):
                pass

def screen_layout(trace=None):
    return _windows_screens() if IS_WINDOWS else _linux_screens()

def find_screen(x,y,screens):
    for item in screens:
        if item['x'] <= x < item['x']+item['w'] and item['y'] <= y < item['y']+item['h']:
            return item['name']
    return None

def layout_key(screens):
    return [{k: s[k] for k in ('name','x','y','w','h')} for s in screens]

def desktop_bounds(screens):
    return (min(s['x'] for s in screens), min(s['y'] for s in screens), max(s['x']+s['w'] for s in screens), max(s['y']+s['h'] for s in screens))

def pointer_position(trace=None):
    if IS_WINDOWS:
        from ctypes import wintypes
        class POINT(ctypes.Structure):
            _fields_ = [('x',wintypes.LONG),('y',wintypes.LONG)]
        point=POINT()
        user32 = _windows_api()
        user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
        user32.GetCursorPos.restype = wintypes.BOOL
        if not user32.GetCursorPos(ctypes.byref(point)):
            raise RuntimeError('GetCursorPos failed')
        return point.x,point.y
    out=run_cmd('kdotool','getmouselocation',trace=trace,quiet=True)
    mx=re.search(r'\bx\s*[:=]\s*(-?\d+)',out,re.I)
    my=re.search(r'\by\s*[:=]\s*(-?\d+)',out,re.I)
    if not (mx and my):
        raise RuntimeError('Unable to parse kdotool pointer: '+out.strip()[:150])
    return int(mx.group(1)),int(my.group(1))

def move_to(point, trace=None):
    x,y = point
    if IS_WINDOWS:
        if trace:
            trace('WIN32',f'SetCursorPos global=({x},{y})')
        user32 = _windows_api()
        user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
        user32.SetCursorPos.restype = ctypes.c_int
        if not user32.SetCursorPos(int(x),int(y)):
            raise RuntimeError('SetCursorPos failed')
    else:
        run_cmd('waytool','move-global',str(x),str(y),timeout=20,trace=trace)

def click_at(point, trace=None):
    if IS_WINDOWS:
        from ctypes import wintypes
        # SendInput uses the current pointer position after verified SetCursorPos.
        ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p)==8 else ctypes.c_ulong
        class MOUSEINPUT(ctypes.Structure):
            _fields_=[('dx',wintypes.LONG),('dy',wintypes.LONG),('mouseData',wintypes.DWORD),('dwFlags',wintypes.DWORD),('time',wintypes.DWORD),('dwExtraInfo',ULONG_PTR)]
        class INPUTDATA(ctypes.Union):
            _fields_=[('mi',MOUSEINPUT)]
        class INPUT(ctypes.Structure):
            _anonymous_=('data',)
            _fields_=[('type',wintypes.DWORD),('data',INPUTDATA)]
        user32=_windows_api()
        user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
        user32.SendInput.restype = wintypes.UINT
        for flags in (0x0002,0x0004):
            inp=INPUT(); inp.type=0; inp.mi=MOUSEINPUT(0,0,0,flags,0,0)
            sent=user32.SendInput(1,ctypes.byref(inp),ctypes.sizeof(inp))
            if sent!=1:
                raise RuntimeError('Windows SendInput failed (another elevated application may block it)')
            time.sleep(.045)
        if trace:
            trace('WIN32','SendInput LEFTDOWN / LEFTUP at '+str(point))
    else:
        run_cmd('waytool','click-global',str(point[0]),str(point[1]),timeout=20,trace=trace)

def linux_browser_audio_state(browser):
    try:
        output=run_cmd('pactl','list','sink-inputs',timeout=8)
    except RuntimeError as exc:
        return None,str(exc)
    for block in output.split('Sink Input #')[1:]:
        meta=dict(re.findall(r'^\s*(application\.(?:name|process\.binary))\s*=\s*"([^"]+)"',block,flags=re.M|re.I))
        properties=[meta.get('application.process.binary',''),meta.get('application.name','')]
        if not any(_matches(p.lower(),browser,'linux') for p in properties):
            continue
        if re.search(r'\bCorked:\s*no\b',block,re.I):
            return True,None
    return False,None

def init_audio_thread():
    if IS_WINDOWS:
        import comtypes
        comtypes.CoInitialize()

def close_audio_thread():
    if IS_WINDOWS:
        import comtypes
        comtypes.CoUninitialize()

_windows_audio_local = threading.local()

def windows_browser_audio_state(browser):
    try:
        import comtypes
        from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
        sessions = AudioUtilities.GetAllSessions()
        active = False
        for session in sessions:
            process = session.Process
            if process is None:
                continue
            try:
                name = process.name().lower()
            except Exception:
                continue
            if _matches(name, browser, 'windows') and int(session.State) == 1:
                active = True
        if not active:
            _windows_audio_local.last_heard = None
            _windows_audio_local.browser = browser
            return False, None

        # Per-app ACTIVE state alone is not a reliable silence detector.
        # Combine it with peak activity of the currently selected speaker.
        # The endpoint peak is shared by *all* apps, not browser-isolated.
        device = AudioUtilities.GetSpeakers()
        if device is None:
            return None, 'No default Windows audio output device is available'
        interface = device._dev.Activate(IAudioMeterInformation._iid_, comtypes.CLSCTX_ALL, None)
        meter = interface.QueryInterface(IAudioMeterInformation)
        peak = float(meter.GetPeakValue())
        if _windows_audio_local.__dict__.get('browser') != browser:
            _windows_audio_local.browser = browser
            _windows_audio_local.last_heard = None
        now = time.monotonic()
        if peak >= 0.006:
            _windows_audio_local.last_heard = now
        previous = _windows_audio_local.__dict__.get('last_heard')
        return previous is not None and now - previous < 0.8, None
    except Exception as exc:
        return None, f'Windows audio meter unavailable: {type(exc).__name__}: {exc}'

def browser_audio_state(browser):
    return windows_browser_audio_state(browser) if IS_WINDOWS else linux_browser_audio_state(browser)

def pointer_health(trace=None):
    if IS_WINDOWS:
        return f'Windows SendInput ready; pointer {pointer_position()}'
    result=run_cmd('waytool','monitors',timeout=20,trace=trace)
    return result.strip()

def diagnostics():
    out=[]
    out.append(('PLATFORM',f'os={os.name} system={os.environ.get("XDG_SESSION_TYPE","Windows" if IS_WINDOWS else "unset")}'))
    out.append(('POINTER',f'position={pointer_position()}'))
    screens=screen_layout()
    out.append(('DISPLAY',f'active={len(screens)} layout={layout_key(screens)} bounds={desktop_bounds(screens)}'))
    out.append(('POINTER',pointer_health()[:1000]))
    return out
