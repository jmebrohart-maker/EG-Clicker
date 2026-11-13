"""Native Windows entry point, diagnostics, and single-instance handling."""
import argparse
import contextlib
import ctypes
import json
import os
from pathlib import Path
import sys
import traceback

MUTEX = r'Local\EhrhartGroup.EGClicker.Windows'


def _error(message, interactive=True):
    folder = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'EG-Clicker' / 'logs'
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / 'startup-errors.log').open('a', encoding='utf-8') as stream:
        stream.write(message + '\n')
    if os.name == 'nt' and interactive:
        api = ctypes.WinDLL(str(Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32' / 'user32.dll'))
        api.MessageBoxW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint]
        api.MessageBoxW(None, message[-1500:] + '\n\nDetails: ' + str(folder / 'startup-errors.log'), 'EG-Clicker startup error', 0x10)
    else:
        print(message, file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(description='EG-Clicker for Windows')
    parser.add_argument('--diagnose', action='store_true', help='Write a read-only desktop/audio diagnostic report')
    parser.add_argument('--self-test', action='store_true', help='Check bundled runtime, Tk and Win32 ABI without sending input')
    parser.add_argument('--output', type=Path, help='Diagnostic/self-test output file')
    args = parser.parse_args(argv)
    if os.name != 'nt':
        parser.error('This edition requires Windows. Use the Fedora edition on Linux.')
    if sys.stdout is None:sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:sys.stderr = open(os.devnull, 'w')
    from eg_platform import init_desktop, init_audio_thread, close_audio_thread, browser_audio_state, LOG_FILE, INPUT, POINT, screen_layout, pointer_position, _kernel32
    init_desktop()
    from eg_app import App, VERSION, diagnose_cli
    import tkinter as tk
    if args.self_test:
        import comtypes
        from pycaw.pycaw import AudioUtilities
        from pycaw.api.endpointvolume import IAudioMeterInformation
        from launcher import browser_executable
        root = tk.Tk();root.withdraw();root.update();root.destroy()
        expected = 40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28
        if ctypes.sizeof(INPUT) != expected or ctypes.sizeof(POINT) != 8:
            raise RuntimeError('Unexpected Win32 input structure layout')
        report = dict(version=VERSION, frozen=bool(getattr(sys, 'frozen', False)), python=sys.version,
                      tkinter=tk.TkVersion, input_size=ctypes.sizeof(INPUT), runtime='ok', input_sent=False)
        output = args.output or LOG_FILE.with_name('self-test.json')
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        return 0
    if args.diagnose:
        output = args.output or LOG_FILE.with_name('diagnostics.txt')
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('w', encoding='utf-8') as stream, contextlib.redirect_stdout(stream):
            diagnose_cli()
            try:
                init_audio_thread()
                from eg_app import load_browser
                print('Browser session audio:', browser_audio_state(load_browser()))
            finally:
                close_audio_thread()
        return 0
    kernel = _kernel32()
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
    kernel.CreateMutexW.restype = ctypes.c_void_p
    ctypes.set_last_error(0)
    handle = kernel.CreateMutexW(None, False, MUTEX)
    if not handle:raise RuntimeError('Could not create the application instance lock.')
    try:
        if ctypes.get_last_error() == 183:
            _error('EG-Clicker is already running. Restore its window from the taskbar.')
            return 0
        root = tk.Tk();App(root);root.mainloop()
        return 0
    finally:
        kernel.CloseHandle(handle)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        details = traceback.format_exc()
        if '--output' in sys.argv:
            try:
                output = Path(sys.argv[sys.argv.index('--output')+1])
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(json.dumps({'error':details}, indent=2), encoding='utf-8')
            except Exception:
                pass
        _error(details, interactive=not ('--self-test' in sys.argv or '--diagnose' in sys.argv))
        raise SystemExit(1)
