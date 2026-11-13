"""Windows desktop integration: explicit Win32 ABI and browser-session audio."""
from __future__ import annotations
import ctypes as C
from functools import lru_cache
import os
from pathlib import Path

IS_WINDOWS = os.name == 'nt'
BROWSERS = ('Firefox', 'Chrome', 'Edge', 'Chromium', 'Brave', 'Opera', 'Vivaldi', 'Any Browser')
WINDOWS_NAMES = {
    'Firefox': ('firefox.exe',), 'Chrome': ('chrome.exe',), 'Edge': ('msedge.exe',),
    'Chromium': ('chromium.exe',), 'Brave': ('brave.exe',),
    'Opera': ('opera.exe',), 'Vivaldi': ('vivaldi.exe',),
}
CONFIG = Path(os.environ.get('APPDATA', str(Path.home()))) / 'EG-Clicker' / 'config.json'
LEGACY_CONFIG = Path.home() / '.eg-clicker-legacy-unused'
LOG_FILE = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'EG-Clicker' / 'logs' / 'eg-clicker.log'
LONG, DWORD, UINT, BOOL = C.c_int32, C.c_uint32, C.c_uint32, C.c_int32
HANDLE = C.c_void_p
ULONG_PTR = C.c_uint64 if C.sizeof(C.c_void_p) == 8 else C.c_uint32

class POINT(C.Structure):
    _fields_ = [('x', LONG), ('y', LONG)]
class RECT(C.Structure):
    _fields_ = [('left', LONG), ('top', LONG), ('right', LONG), ('bottom', LONG)]
class MONITORINFOEXW(C.Structure):
    _fields_ = [('cbSize', DWORD), ('rcMonitor', RECT), ('rcWork', RECT), ('dwFlags', DWORD), ('szDevice', C.c_wchar * 32)]
class FILETIME(C.Structure):
    _fields_ = [('low', DWORD), ('high', DWORD)]
class MOUSEINPUT(C.Structure):
    _fields_ = [('dx', LONG), ('dy', LONG), ('mouseData', DWORD), ('dwFlags', DWORD), ('time', DWORD), ('dwExtraInfo', ULONG_PTR)]
class KEYBDINPUT(C.Structure):
    _fields_ = [('wVk', C.c_uint16), ('wScan', C.c_uint16), ('dwFlags', DWORD), ('time', DWORD), ('dwExtraInfo', ULONG_PTR)]
class HARDWAREINPUT(C.Structure):
    _fields_ = [('uMsg', DWORD), ('wParamL', C.c_uint16), ('wParamH', C.c_uint16)]
class INPUTDATA(C.Union):
    _fields_ = [('mi', MOUSEINPUT), ('ki', KEYBDINPUT), ('hi', HARDWAREINPUT)]
class INPUT(C.Structure):
    _anonymous_ = ('data',)
    _fields_ = [('type', DWORD), ('data', INPUTDATA)]


def _matches(name, browser, platform='windows'):
    choices = WINDOWS_NAMES.values() if browser == 'Any Browser' else (WINDOWS_NAMES.get(browser, ()),)
    return name.lower() in {token for names in choices for token in names}


def _library(name):
    if not IS_WINDOWS:
        raise RuntimeError('This edition requires Windows.')
    return C.WinDLL(str(Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32' / name), use_last_error=True)


@lru_cache(maxsize=1)
def _user32():
    api = _library('user32.dll')
    signatures = {
        'GetCursorPos': ([C.POINTER(POINT)], BOOL),
        'SetCursorPos': ([C.c_int, C.c_int], BOOL),
        'SendInput': ([UINT, C.POINTER(INPUT), C.c_int], UINT),
        'GetForegroundWindow': ([], HANDLE),
        'WindowFromPoint': ([POINT], HANDLE),
        'GetAncestor': ([HANDLE, UINT], HANDLE),
        'GetWindowRect': ([HANDLE, C.POINTER(RECT)], BOOL),
        'GetWindowThreadProcessId': ([HANDLE, C.POINTER(DWORD)], DWORD),
        'GetClassNameW': ([HANDLE, C.c_wchar_p, C.c_int], C.c_int),
        'GetMonitorInfoW': ([HANDLE, C.POINTER(MONITORINFOEXW)], BOOL),
    }
    for name, (arguments, result) in signatures.items():
        function = getattr(api, name); function.argtypes = arguments; function.restype = result
    return api


@lru_cache(maxsize=1)
def _kernel32():
    api = _library('kernel32.dll')
    for name, arguments, result in (
        ('OpenProcess', [DWORD, BOOL, DWORD], HANDLE),
        ('CloseHandle', [HANDLE], BOOL),
        ('QueryFullProcessImageNameW', [HANDLE, DWORD, C.c_wchar_p, C.POINTER(DWORD)], BOOL),
        ('GetProcessTimes', [HANDLE] + [C.POINTER(FILETIME)] * 4, BOOL),
    ):
        function = getattr(api, name); function.argtypes = arguments; function.restype = result
    return api


def init_desktop():
    try:
        api = _user32()
        api.SetProcessDpiAwarenessContext.argtypes = [HANDLE]
        api.SetProcessDpiAwarenessContext.restype = BOOL
        if api.SetProcessDpiAwarenessContext(HANDLE(-4)):
            return
    except (OSError, AttributeError):
        pass
    try:
        api = _library('shcore.dll')
        api.SetProcessDpiAwareness.argtypes = [C.c_int]
        api.SetProcessDpiAwareness(2)
    except (OSError, AttributeError):
        pass


def screen_layout(trace=None):
    api = _user32(); found = []
    callback_type = C.WINFUNCTYPE(BOOL, HANDLE, HANDLE, C.POINTER(RECT), C.c_ssize_t)
    @callback_type
    def callback(monitor, _dc, _rect, _data):
        info = MONITORINFOEXW(); info.cbSize = C.sizeof(info)
        if api.GetMonitorInfoW(monitor, C.byref(info)):
            r = info.rcMonitor
            if r.right > r.left and r.bottom > r.top:
                found.append(dict(name=info.szDevice, x=r.left, y=r.top, w=r.right-r.left, h=r.bottom-r.top))
        return 1
    api.EnumDisplayMonitors.argtypes = [HANDLE, C.POINTER(RECT), callback_type, C.c_ssize_t]
    api.EnumDisplayMonitors.restype = BOOL
    if not api.EnumDisplayMonitors(None, None, callback, 0) or not found:
        raise RuntimeError('Windows could not enumerate active displays.')
    return sorted(found, key=lambda s:(s['x'], s['y'], s['name']))


def find_screen(x, y, screens):
    return next((s['name'] for s in screens if s['x'] <= x < s['x']+s['w'] and s['y'] <= y < s['y']+s['h']), None)


def layout_key(screens):
    return [{k:s[k] for k in ('name', 'x', 'y', 'w', 'h')} for s in screens]


def desktop_bounds(screens):
    return (min(s['x'] for s in screens), min(s['y'] for s in screens), max(s['x']+s['w'] for s in screens), max(s['y']+s['h'] for s in screens))


def display_point(point):
    return f'({point[0]}, {point[1]})'


def pointer_position(trace=None):
    point = POINT()
    if not _user32().GetCursorPos(C.byref(point)):
        raise RuntimeError('Windows could not read the pointer position.')
    return point.x, point.y


def move_to(point, trace=None):
    if not _user32().SetCursorPos(int(point[0]), int(point[1])):
        raise RuntimeError('Windows could not move the pointer; check the active desktop.')
    if trace:trace('POINTER', 'SetCursorPos ' + str(point))


def click_at(point, trace=None):
    api = _user32()
    events = (INPUT * 2)()
    events[0].type = events[1].type = 0
    events[0].mi.dwFlags, events[1].mi.dwFlags = 0x0002, 0x0004
    count = api.SendInput(2, events, C.sizeof(INPUT))
    if count != 2:
        if count == 1:
            # Release a partially sent button-down; never retry the click itself.
            api.SendInput(1, C.pointer(events[1]), C.sizeof(INPUT))
        raise RuntimeError('Windows blocked input. EG-Clicker cannot control elevated apps from a normal user session.')
    if trace:trace('CLICK', 'SendInput left down/up at verified point ' + str(point))


def pointer_health(trace=None):
    return f'Win32 pointer ready at {pointer_position()}'


def init_audio_thread():
    import comtypes
    comtypes.CoInitialize()


def close_audio_thread():
    import comtypes
    comtypes.CoUninitialize()


def _audio_backend():
    from pycaw.pycaw import AudioUtilities
    from pycaw.api.endpointvolume import IAudioMeterInformation
    return AudioUtilities.GetAllSessions(), IAudioMeterInformation


def browser_audio_state(browser):
    try:
        sessions, meter_type = _audio_backend()
        failures = []
        for session in sessions:
            process = session.Process
            if process is None:
                continue
            try:
                name = process.name().lower()
            except Exception:
                continue
            if not _matches(name, browser) or int(session.State) != 1:
                continue
            try:
                meter = session._ctl.QueryInterface(meter_type)
                if float(meter.GetPeakValue()) >= 0.006:
                    return True, None
            except Exception as exc:
                failures.append(type(exc).__name__)
        if failures:
            return None, 'Browser-session audio meter unavailable: ' + ', '.join(sorted(set(failures)))
        return False, None
    except Exception as exc:
        return None, f'Windows audio unavailable: {type(exc).__name__}: {exc}'


def _process_identity(pid):
    api = _kernel32(); handle = api.OpenProcess(0x1000, False, pid)
    if not handle:
        raise RuntimeError('Cannot inspect the browser process; it may be elevated or closed.')
    try:
        length = DWORD(32768); image = C.create_unicode_buffer(length.value)
        if not api.QueryFullProcessImageNameW(handle, 0, image, C.byref(length)):
            raise RuntimeError('Cannot identify the browser executable.')
        created, exited, kernel, user = FILETIME(), FILETIME(), FILETIME(), FILETIME()
        if not api.GetProcessTimes(handle, C.byref(created), C.byref(exited), C.byref(kernel), C.byref(user)):
            raise RuntimeError('Cannot identify the browser process lifetime.')
        return Path(image.value).name.lower(), str((created.high << 32) | created.low)
    finally:
        api.CloseHandle(handle)


def window_snapshot():
    api = _user32(); point = POINT(*pointer_position())
    window = api.GetAncestor(api.WindowFromPoint(point), 2)
    active = api.GetAncestor(api.GetForegroundWindow(), 2)
    if not window or not active:
        raise RuntimeError('The target must be over a normal application window.')
    rect, pid = RECT(), DWORD()
    if not api.GetWindowRect(window, C.byref(rect)) or not api.GetWindowThreadProcessId(window, C.byref(pid)):
        raise RuntimeError('Cannot verify the target window.')
    klass = C.create_unicode_buffer(256)
    if not api.GetClassNameW(window, klass, len(klass)):
        raise RuntimeError('Cannot verify the target window class.')
    image, started = _process_identity(pid.value)
    return dict(id=str(window), pid=pid.value, active=str(active), image=image,
                started=started, geometry=[rect.left, rect.top, rect.right-rect.left, rect.bottom-rect.top],
                pointer=[point.x, point.y], **{'class':klass.value.lower()})
