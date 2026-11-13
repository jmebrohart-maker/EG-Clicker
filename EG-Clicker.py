#!/usr/bin/env python3
"""EG-Clicker 2.0 • Ehrhart Group LLC • Fedora Wayland / Windows 11.

Browser audio-stop clicker with persistent target, safe pointer verification,
and a copyable, auto-saved diagnostic log.

Run as your normal desktop user (not sudo on Fedora):
    python3 ~/EG-Clicker.py
    python3 ~/EG-Clicker.py --diagnose

Fedora requires: tkinter, pactl, kdotool, kscreen-doctor, waytool.
Windows requires: tkinter and pycaw for Core Audio sessions.  The embedded brand icon needs no extra image file.
"""
from __future__ import annotations

import base64
from collections import deque
from datetime import datetime
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from tkinter import filedialog, scrolledtext, messagebox

VERSION = '3.0.2'
APP_TITLE = 'EG-Clicker • Ehrhart Group LLC'
from eg_platform import (IS_WINDOWS, BROWSERS, CONFIG, LEGACY_CONFIG, LOG_FILE,
    run_cmd, pointer_position, parse_screens_json, parse_screens_text, screen_layout,
    find_screen, layout_key, desktop_bounds, move_to, click_at,
    browser_audio_state, init_audio_thread, close_audio_thread, init_desktop, pointer_health)
# Defaults match the last known-working Fedora 44 release.
DEFAULT_RELIABILITY = {'retries_enabled': False, 'retry_count': 1,
                       'tolerance_px': 4, 'settle_ms': 200}
MAX_RETRIES = 5
MAX_TOLERANCE = 12
from window_guard import capture_window, verify_window, matches_saved_browser


NAVY = '#0a1634'
NAVY2 = '#10224a'
PANEL = '#152853'
PANEL2 = '#1a3261'
BLUE = '#3b82f6'
SKY = '#80b9ff'
WHITE = '#f4f7ff'
MUTED = '#b5c5e4'
YELLOW = '#ffd891'
GREEN = '#75e0b0'
RED = '#ff91a0'
LINE = '#31517f'

LOGO_BASE64 = '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'


def display_point(p):
    return f'({p[0]}, {p[1]})'


def read_config(path=None):
    path = CONFIG if path is None else path
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def save_launch_url(url):
    from urllib.parse import urlsplit
    url = url.strip()
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise ValueError('Enter a full http:// or https:// website URL.')
    record = read_config()
    record['launch_url'] = url
    _secure_atomic_json(CONFIG, record)
    return url


def load_target():
    for path in (CONFIG, LEGACY_CONFIG):
        try:
            item = read_config(path)
            if isinstance(item.get('layout'), list) and 'x' in item and 'y' in item:
                return (int(item['x']), int(item['y'])), item['layout'], str(path)
        except (OSError, ValueError, TypeError):
            pass
    return None, None, None


def load_browser():
    try:
        name = read_config(CONFIG).get('browser', 'Firefox')
        return name if name in BROWSERS else 'Firefox'
    except (OSError, ValueError, TypeError):
        return 'Firefox'


def _ensure_private_dir(path):
    """Create state directories with private Unix mode; reject directory symlinks."""
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink() or not path.is_dir():
        raise OSError(f'Unsafe state directory: {path}')
    if not IS_WINDOWS:
        os.chmod(path, 0o700)


def _secure_atomic_json(path, record):
    """Fresh exclusive temporary file, no symlink following, atomic replacement."""
    import tempfile
    _ensure_private_dir(path.parent)
    fd, tmp = tempfile.mkstemp(prefix='.eg-config-', suffix='.tmp', dir=str(path.parent))
    try:
        if not IS_WINDOWS:
            os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(json.dumps(record, indent=2) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def save_target_record(point, screens, browser='Firefox', window=None):
    _ensure_private_dir(CONFIG.parent)
    try:
        record = read_config(CONFIG)
        if not isinstance(record, dict):
            record = {}
    except (OSError, ValueError, TypeError):
        record = {}
    record.update({'schema': 10, 'x': point[0], 'y': point[1],
                   'layout': layout_key(screens), 'browser': browser, 'target_window': window})
    _secure_atomic_json(CONFIG, record)
    return record


def save_browser_choice(browser):
    _ensure_private_dir(CONFIG.parent)
    try:
        record = read_config(CONFIG)
    except (OSError, ValueError, TypeError):
        record = {}
    record['browser'] = browser
    if not matches_saved_browser(record.get('target_window'), browser):
        record.pop('target_window', None)
    _secure_atomic_json(CONFIG, record)


def normalize_reliability(raw):
    raw = raw if isinstance(raw, dict) else {}
    def number(key, default, lo, hi):
        try:
            n = int(raw.get(key, default))
        except (ValueError, TypeError, OverflowError):
            n = default
        return max(lo, min(hi, n))
    return {
        'retries_enabled': raw.get('retries_enabled', False) is True,
        'retry_count': number('retry_count', 1, 0, MAX_RETRIES),
        'tolerance_px': number('tolerance_px', 4, 0, MAX_TOLERANCE),
        'settle_ms': number('settle_ms', 200, 100, 700),
    }


def load_reliability():
    try:
        data = read_config(CONFIG)
        return normalize_reliability(data.get('pointer_reliability', {}))
    except (OSError, ValueError, TypeError, AttributeError):
        return dict(DEFAULT_RELIABILITY)


def save_reliability(settings):
    settings = normalize_reliability(settings)
    try:
        data = read_config(CONFIG)
        if not isinstance(data, dict):
            data = {}
    except (OSError, ValueError, TypeError):
        data = {}
    data['pointer_reliability'] = settings
    _secure_atomic_json(CONFIG, data)
    return settings


class LogWriter:
    """Thread-safe rotating log. Linux file opens reject symlinks."""
    def __init__(self, path=LOG_FILE):
        self.path = path
        self.lock = threading.Lock()
        self.error = None
        try:
            _ensure_private_dir(path.parent)
            if path.is_symlink():
                raise OSError('Refusing symbolic-link log file')
            if path.exists() and path.stat().st_size > 1_500_000:
                old = path.with_name('eg-clicker.previous.log')
                if old.is_symlink():
                    raise OSError('Refusing symbolic-link rotated log')
                os.replace(path, old)
            fd = self._open_append()
            os.close(fd)
        except OSError as exc:
            self.error = str(exc)

    def _open_append(self):
        flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
        if not IS_WINDOWS:
            flags |= getattr(os, 'O_NOFOLLOW', 0)
        fd = os.open(self.path, flags, 0o600)
        if not IS_WINDOWS:
            import stat
            mode = os.fstat(fd).st_mode
            if not stat.S_ISREG(mode) or os.fstat(fd).st_nlink != 1:
                os.close(fd)
                raise OSError('Refusing unsafe log destination')
            os.fchmod(fd, 0o600)
        return fd

    def write(self, severity, message):
        stamp = datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S.%f%z')
        lines = message.replace('\r', '').split('\n')
        entries = [f'{stamp} [{severity:<7}] {line}' for line in lines]
        with self.lock:
            if self.error is None:
                try:
                    with os.fdopen(self._open_append(), 'a', encoding='utf-8') as stream:
                        stream.write('\n'.join(entries) + '\n')
                except OSError as exc:
                    self.error = str(exc)
        return '\n'.join(entries)


class App:
    def __init__(self, root):
        self.root = root
        self.running = True
        self.armed = False
        self.arming = False
        self.arm_generation = 0
        self.log_window = None
        self.last_callback_error = None
        self.audio = None
        self.target, self.saved_layout, source = load_target()
        self.target_window = read_config().get('target_window')
        self.browser = load_browser()
        self.browser_var = tk.StringVar(value=self.browser)
        self.launch_url_var = tk.StringVar(value=read_config().get('launch_url', 'https://www.google.com'))
        self.reliability = load_reliability()
        self.retry_enabled_var = tk.BooleanVar(value=self.reliability['retries_enabled'])
        self.retry_count_var = tk.StringVar(value=str(self.reliability['retry_count']))
        self.tolerance_var = tk.StringVar(value=str(self.reliability['tolerance_px']))
        self.settle_var = tk.StringVar(value=str(self.reliability['settle_ms']))
        self.reliability_open = False
        self.verified = False
        self.click_count = 0
        self.action_lock = threading.Lock()
        self.events = queue.Queue()
        self.filelog = LogWriter()
        self.history = deque(maxlen=1600)
        self.last_audio_error = ''
        self.last_audio_state = 'CHECKING'
        self.note_message = 'Save the Next button position, then press Arm / Disarm to start.'
        self.note_bad = False
        self.move_result = 'UNTESTED'

        root.title(f'{APP_TITLE} • {VERSION}')
        root.geometry('910x530')
        root.minsize(740, 445)
        root.configure(bg=NAVY)

        self.build_ui()
        root.report_callback_exception = self.callback_error
        self.log('INFO', f'EG-Clicker {VERSION} started. OS={os.name}; browser={self.browser}.')
        self.log('INFO', f'session={os.environ.get("XDG_SESSION_TYPE", "unset")} '
                 f'uid={os.getuid() if hasattr(os, "getuid") else "Windows"} DISPLAY={os.environ.get("DISPLAY", "unset")} '
                 f'WAYLAND_DISPLAY={os.environ.get("WAYLAND_DISPLAY", "unset")}')
        self.log('INFO', 'Automatic log file: ' + str(LOG_FILE))
        if self.filelog.error:
            self.log('WARN', 'Cannot write automatic log: ' + self.filelog.error)
        if source:
            self.log('TARGET', f'Loaded saved location {self.target} from {source}; ready for use after checking monitor layout.')
        self.log('INFO', 'Movement checks are optional; every actual click still verifies the live pointer position.')
        self.log('SETTINGS', f'Pointer reliability: {self.reliability}')
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.refresh()
        self.refresh_diagnostics()
        threading.Thread(target=self.audio_watcher, name='EG-AudioWatcher', daemon=True).start()

    def build_ui(self):
        header = tk.Frame(self.root, bg=WHITE, padx=18, pady=12)
        header.pack(fill='x', padx=15, pady=(15, 10))
        try:
            self.logo = tk.PhotoImage(data=LOGO_BASE64)
            tk.Label(header, image=self.logo, bg=WHITE).pack(side='left', padx=(4, 16))
            self.root.iconphoto(True, self.logo)
        except tk.TclError:
            pass
        h = tk.Frame(header, bg=WHITE)
        h.pack(side='left', fill='x', expand=True)
        tk.Label(h, text='EG-Clicker', bg=WHITE, fg=NAVY,
                 font=('Sans', 25, 'bold'), anchor='w').pack(fill='x')
        tk.Label(h, text='An audio controlled auto clicker', bg=WHITE, fg='#26518f',
                 font=('Sans', 11, 'bold'), anchor='w').pack(fill='x', pady=(0, 3))
        company_link = tk.Label(h, text='Ehrhart Group LLC / Tech and infrastructure',
                 bg=WHITE, fg='#174f9f', font=('Sans', 10, 'underline'), anchor='w',
                 cursor='hand2')
        company_link.pack(fill='x')
        company_link.bind('<Button-1>', lambda _event: webbrowser.open('https://ehrhartgroup.us'))
        company_link.bind('<Enter>', lambda _event: company_link.configure(fg='#3383df'))
        company_link.bind('<Leave>', lambda _event: company_link.configure(fg='#174f9f'))
        tk.Label(header, text=f'v{VERSION}', bg=WHITE, fg='#526a93',
                 font=('Sans', 10, 'bold')).pack(side='right', anchor='ne', padx=4)

        statuses = tk.Frame(self.root, bg=NAVY)
        statuses.pack(fill='x', padx=15, pady=4)

        self.target_label = self.status_tile(statuses, 'SAVED NEXT TARGET', 0)
        self.audio_label = self.status_tile(statuses, 'SELECTED BROWSER AUDIO', 1)
        self.pointer_label = self.status_tile(statuses, 'POINTER CONTROL', 2)

        browser_bar = tk.Frame(self.root, bg=NAVY2, padx=14, pady=8,
                               highlightbackground=LINE, highlightthickness=1)
        browser_bar.pack(fill='x', padx=15, pady=(8, 0))
        tk.Label(browser_bar, text='MONITOR BROWSER', bg=NAVY2, fg=WHITE,
                 font=('Sans', 10, 'bold')).pack(side='left', padx=(2, 14))
        dropdown = tk.OptionMenu(browser_bar, self.browser_var, *BROWSERS,
                                 command=self.change_browser)
        dropdown.configure(bg=PANEL2, fg=WHITE, activebackground=BLUE,
                           activeforeground=WHITE, relief=tk.FLAT, highlightthickness=0,
                           font=('Sans', 10, 'bold'), width=17)
        dropdown['menu'].configure(bg=PANEL2, fg=WHITE, font=('Sans', 10))
        dropdown.pack(side='left')
        tk.Label(browser_bar, text='Audio stop → 2s quiet → saved click', bg=NAVY2,
                 fg=MUTED, font=('Sans', 9)).pack(side='right', padx=8)

        launch = tk.Frame(self.root, bg=NAVY2, padx=15, pady=6)
        launch.pack(fill='x', padx=15)
        tk.Label(launch, text='Website', bg=NAVY2, fg=WHITE).pack(side='left')
        tk.Entry(launch, textvariable=self.launch_url_var, bg=PANEL2, fg=WHITE,
                 insertbackground=WHITE).pack(side='left', fill='x', expand=True, padx=10)
        tk.Button(launch, text='Open Logs', command=self.show_logs,
                  bg=PANEL2, fg=WHITE, padx=10).pack(side='right', padx=(5, 0))
        tk.Button(launch, text='Launch Browser', command=self.launch_browser,
                  bg=BLUE, fg=WHITE, padx=12).pack(side='right')

        ctl = tk.Frame(self.root, bg=NAVY2, padx=14, pady=11, highlightbackground=LINE, highlightthickness=1)
        ctl.pack(fill='x', padx=15, pady=(10, 7))
        tk.Label(ctl, text='TARGET & AUTOMATION', bg=NAVY2, fg=WHITE,
                 font=('Sans', 11, 'bold'), anchor='w').grid(row=0, column=0, sticky='w', columnspan=3, pady=(0, 8))
        for idx in range(3):
            ctl.grid_columnconfigure(idx, weight=1, uniform='ctl')
        # Everyday controls stay visible; tests and diagnostics are optional.
        primary = [
            ('Save Next (4s)', self.save_delayed),
            ('Arm / Disarm', self.toggle_arm),
            ('Testing & Troubleshooting ▼', self.toggle_testing),
        ]
        for i, (caption, callback) in enumerate(primary):
            button = tk.Button(ctl, text=caption, command=callback,
                               bg='#2556a0' if i == 1 else PANEL2, fg=WHITE,
                               activebackground=BLUE, activeforeground=WHITE,
                               relief=tk.FLAT, bd=0, font=('Sans', 10, 'bold'),
                               padx=10, pady=9, cursor='hand2')
            button.grid(row=1, column=i, padx=5, pady=5, sticky='ew')
            if i == 1:
                self.arm_button = button
            if i == 2:
                self.testing_button = button

        self.testing_frame = tk.Frame(self.root, bg=NAVY2, padx=14, pady=9,
                                      highlightbackground=LINE, highlightthickness=1)
        self.testing_open = False
        tk.Label(self.testing_frame, text='OPTIONAL POINTER TESTS', bg=NAVY2, fg=WHITE,
                 font=('Sans', 10, 'bold')).pack(anchor='w', pady=(0, 6))
        test_row = tk.Frame(self.testing_frame, bg=NAVY2)
        test_row.pack(fill='x')
        tests = [('Move Only (No Click)', self.test_move),
                 ('Test Saved Click', self.test_click),
                 ('Check Pointer / Displays', self.refresh_diagnostics),
                 ('Show Diagnostics ▼', self.toggle_diagnostics)]
        for caption, callback in tests:
            button = tk.Button(test_row, text=caption, command=callback, bg=PANEL2, fg=WHITE,
                               activebackground=BLUE, activeforeground=WHITE, relief=tk.FLAT,
                               font=('Sans', 9, 'bold'), padx=9, pady=7, cursor='hand2')
            button.pack(side='left', padx=(0, 7), pady=2)
            if caption.startswith('Show Diagnostics'):
                self.diagnostics_button = button

        # Separate, collapsed advanced settings panel (not the testing section).
        self.reliability_button = tk.Button(self.root,
            text='Pointer Reliability Settings ▼', command=self.toggle_reliability,
            bg=NAVY2, fg=SKY, activebackground=PANEL2, activeforeground=WHITE,
            relief=tk.FLAT, font=('Sans', 10, 'bold'), cursor='hand2', pady=7)
        self.reliability_button.pack(fill='x', padx=15, pady=(0, 4))
        self.reliability_frame = tk.Frame(self.root, bg=NAVY2, padx=15, pady=12,
                                         highlightbackground=LINE, highlightthickness=1)
        tk.Label(self.reliability_frame, text='POINTER RELIABILITY • ADVANCED',
                 bg=NAVY2, fg=WHITE, font=('Sans', 11, 'bold')).grid(
                 row=0, column=0, columnspan=3, sticky='w', pady=(0, 10))
        chk = tk.Checkbutton(self.reliability_frame, text='Enable automatic movement retries',
                            variable=self.retry_enabled_var,
                            bg=NAVY2, fg=WHITE, activebackground=NAVY2,
                            activeforeground=WHITE, selectcolor=PANEL2,
                            font=('Sans', 10), anchor='w')
        chk.grid(row=1, column=0, columnspan=3, sticky='w', pady=4)
        for row, (label, variable, values, help_text) in enumerate([
            ('Extra retries', self.retry_count_var, tuple(str(n) for n in range(0, MAX_RETRIES+1)),
             '0–5 extra moves if positioning misses'),
            ('Tolerance (px)', self.tolerance_var, tuple(str(n) for n in range(MAX_TOLERANCE+1)),
             'Max X/Y pixel error; 0 requires exact match'),
            ('Settle delay (ms)', self.settle_var,
             ('100', '150', '200', '250', '300', '400', '500', '700'),
             'Wait after moving before checking coordinates'),
        ], start=2):
            tk.Label(self.reliability_frame, text=label, bg=NAVY2, fg=WHITE,
                     anchor='w', font=('Sans', 10)).grid(row=row, column=0, sticky='w', pady=5)
            opt = tk.OptionMenu(self.reliability_frame, variable, *values)
            opt.configure(bg=PANEL2, fg=WHITE, activebackground=BLUE,
                          activeforeground=WHITE, relief=tk.FLAT, highlightthickness=0,
                          width=8, font=('Sans', 10))
            opt['menu'].configure(bg=PANEL2, fg=WHITE)
            opt.grid(row=row, column=1, sticky='w', padx=(12, 16))
            tk.Label(self.reliability_frame, text=help_text, bg=NAVY2, fg=MUTED,
                     font=('Sans', 9), anchor='w').grid(row=row, column=2, sticky='w')
        self.reliability_frame.grid_columnconfigure(2, weight=1)
        tk.Button(self.reliability_frame, text='Restore Safe Defaults',
                  command=self.reset_reliability, bg=PANEL2, fg=WHITE,
                  activebackground=BLUE, relief=tk.FLAT, font=('Sans', 9),
                  padx=9, pady=6).grid(row=5, column=0, columnspan=2, sticky='w', pady=(10, 0))

        tk.Button(self.reliability_frame, text='Save Settings',
                  command=self.apply_reliability, bg=BLUE, fg=WHITE,
                  padx=12, pady=6).grid(row=5, column=2, sticky='e', pady=(10, 0))

        self.arm_label = tk.Label(ctl, text='DISARMED', bg=NAVY2, fg=RED,
                                   font=('Sans', 10, 'bold'), anchor='w')
        self.arm_label.grid(row=2, column=0, sticky='w', padx=6, pady=(7, 0))
        self.count_label = tk.Label(ctl, text='Clicks sent: 0', bg=NAVY2, fg=MUTED,
                                    font=('Sans', 10), anchor='e')
        self.count_label.grid(row=2, column=1, columnspan=2, sticky='e', padx=6, pady=(7, 0))

        note = tk.Frame(self.root, bg=NAVY, padx=16, pady=2)
        note.pack(fill='x')
        self.note_label = tk.Label(note, text='', bg=NAVY, fg=MUTED, font=('Sans', 10),
                                    wraplength=860, justify='left', anchor='w')
        self.note_label.pack(fill='x')

        logs = tk.Frame(self.root, bg=NAVY2, padx=14, pady=12, highlightbackground=LINE,
                        highlightthickness=1)
        self.diagnostics_frame = logs
        self.diagnostics_open = False
        self._diagnostics_pack_options = {'fill': 'both', 'expand': True,
                                           'padx': 15, 'pady': (6, 10)}
        # Diagnostics remain available but hidden until requested.

        top = tk.Frame(logs, bg=NAVY2)
        top.pack(fill='x', pady=(0, 8))
        tk.Label(top, text='DIAGNOSTIC LOG', bg=NAVY2, fg=WHITE,
                 font=('Sans', 12, 'bold')).pack(side='left')
        tk.Label(top, text='Saved automatically • Copy and paste here for troubleshooting',
                 bg=NAVY2, fg=MUTED, font=('Sans', 9)).pack(side='right')
        self.log_text = scrolledtext.ScrolledText(logs, bg='#071126', fg='#d8e8ff',
                  insertbackground=WHITE, selectbackground='#2460b0', relief=tk.FLAT,
                  font=('DejaVu Sans Mono', 9), wrap='word', padx=10, pady=8,
                  height=7, state='disabled')
        self.log_text.pack(fill='both', expand=True)
        actions = tk.Frame(logs, bg=NAVY2)
        actions.pack(fill='x', pady=(9, 0))
        for title, callback in [('Copy All Logs', self.copy_logs),
                                ('Save Log As…', self.save_logs_as),
                                ('Clear View', self.clear_log_view),
                                ('Refresh Diagnostics', self.refresh_diagnostics)]:
            tk.Button(actions, text=title, command=callback, bg=PANEL2, fg=WHITE,
                      activebackground=BLUE, activeforeground=WHITE, relief=tk.FLAT,
                      font=('Sans', 9), padx=13, pady=6).pack(side='left', padx=(0, 8))
        self.footer = tk.Label(self.root, bg=NAVY, fg=MUTED, font=('Sans', 9), anchor='w',
                               text='Logs: ' + str(LOG_FILE) + '   •   Wrong position = NO CLICK')
        self.footer.pack(fill='x', padx=19, pady=(0, 9))

    def toggle_testing(self):
        if self.testing_open:
            if self.diagnostics_open:
                self.diagnostics_frame.pack_forget()
                self.diagnostics_button.configure(text='Show Diagnostics ▼')
                self.diagnostics_open = False
            self.testing_frame.pack_forget()
            self.testing_open = False
            self.testing_button.configure(text='Testing & Troubleshooting ▼')
            self.resize_panels()
        else:
            # Pack between main controls and the status note.
            self.testing_frame.pack(fill='x', padx=15, pady=(2, 7), before=self.note_label.master)
            self.testing_open = True
            self.testing_button.configure(text='Hide Testing & Troubleshooting ▲')
            self.resize_panels()

    def toggle_reliability(self):
        if self.reliability_open:
            self.reliability_frame.pack_forget()
            self.reliability_button.configure(text='Pointer Reliability Settings ▼')
            self.reliability_open = False
        else:
            self.reliability_frame.pack(fill='x', padx=15, pady=(0, 8),
                                        after=self.reliability_button)
            self.reliability_button.configure(text='Hide Pointer Reliability Settings ▲')
            self.reliability_open = True
        self.resize_panels()

    def resize_panels(self):
        height = 530 + (100 if self.testing_open else 0) + (260 if self.reliability_open else 0)
        if self.diagnostics_open:
            height += 320
        self.root.geometry(f'910x{min(height, 980)}')

    def launch_browser(self):
        try:
            url = save_launch_url(self.launch_url_var.get())
            self.launch_url_var.set(url)
            from launcher import launch_browser
            launch_browser(self.browser, url)
            self.note('INFO', f'Opened {self.browser}. Save Next, then Arm to start monitoring.')
        except (ValueError, OSError, RuntimeError) as exc:
            self.note('ERROR', f'Launch failed: {exc}')

    def apply_reliability(self):
        updated = normalize_reliability({
            'retries_enabled': self.retry_enabled_var.get(),
            'retry_count': self.retry_count_var.get(),
            'tolerance_px': self.tolerance_var.get(),
            'settle_ms': self.settle_var.get(),
        })
        try:
            updated = save_reliability(updated)
        except OSError as exc:
            self.note('ERROR', f'Could not save pointer settings: {exc}')
            return False
        self.armed = False
        self.cancel_arming()
        self.reliability = updated
        self.retry_count_var.set(str(updated['retry_count']))
        self.tolerance_var.set(str(updated['tolerance_px']))
        self.settle_var.set(str(updated['settle_ms']))
        self.note('SETTINGS', 'Settings saved. Re-arm to resume automation.')
        self.log('SETTINGS', f'Updated pointer reliability: {updated}')
        return True

    def reset_reliability(self):
        d = DEFAULT_RELIABILITY
        self.retry_enabled_var.set(d['retries_enabled'])
        self.retry_count_var.set(str(d['retry_count']))
        self.tolerance_var.set(str(d['tolerance_px']))
        self.settle_var.set(str(d['settle_ms']))
        if self.apply_reliability():
            self.note('SETTINGS', 'Restored last known-working pointer defaults.')

    def toggle_diagnostics(self):
        if self.diagnostics_open:
            self.diagnostics_frame.pack_forget()
            self.diagnostics_button.configure(text='Show Diagnostics ▼')
            self.diagnostics_open = False
            self.resize_panels()
        else:
            self.diagnostics_frame.pack(**self._diagnostics_pack_options,
                                        before=self.footer)
            self.diagnostics_button.configure(text='Hide Diagnostics ▲')
            self.diagnostics_open = True
            self.resize_panels()

    def status_tile(self, parent, title, index):
        frame = tk.Frame(parent, bg=NAVY2, highlightbackground=LINE, highlightthickness=1, padx=13, pady=11)
        frame.grid(row=0, column=index, sticky='ew', padx=(0 if index == 0 else 5, 0))
        parent.grid_columnconfigure(index, weight=1, uniform='status')
        tk.Label(frame, text=title, bg=NAVY2, fg=MUTED, font=('Sans', 9, 'bold'),
                 anchor='w').pack(fill='x')
        result = tk.Label(frame, text='Checking…', bg=NAVY2, fg=YELLOW,
                          font=('Sans', 12, 'bold'), anchor='w', justify='left',
                          wraplength=220)
        result.pack(fill='x', pady=(5, 0))
        return result

    def log(self, severity, message):
        # Worker threads write to disk and forward formatted text to Tk's thread.
        lines = self.filelog.write(severity, str(message))
        self.events.put(('log', lines))

    def note(self, severity, message):
        self.log(severity, message)
        self.events.put(('note', (severity, message)))

    def snapshot_diagnostics(self):
        self.log('DIAG', '===== diagnostic snapshot =====')
        self.log('DIAG', f'pointer_reliability={self.reliability}')
        self.log('DIAG', f'platform={os.name} browser={self.browser} saved_target={self.target} '
                 f'verified={self.verified} armed={self.armed}')
        try:
            screens = screen_layout()
            self.log('DISPLAY', f'displays={layout_key(screens)} bounds={desktop_bounds(screens)}')
            self.events.put(('displays', f'{len(screens)} active • ' +
                             ' | '.join(f'{s["name"]} {s["x"]},{s["y"]} {s["w"]}×{s["h"]}' for s in screens)))
            if self.target:
                self.log('TARGET', f'saved={self.target} monitor={find_screen(*self.target, screens)}')
                self.log('TARGET', f'saved_layout_matches={self.saved_layout == layout_key(screens)}')
        except RuntimeError as exc:
            self.note('ERROR', 'Displays: ' + str(exc))
        try:
            self.log('POINTER', f'pointer={pointer_position()}')
            self.log('POINTER', f'health={pointer_health(self.log)[:800]}')
            self.events.put(('pointer', ('READY • ' + ('Win32' if IS_WINDOWS else 'waytool'), GREEN)))
        except RuntimeError as exc:
            self.note('ERROR', 'Pointer: ' + str(exc))
            self.events.put(('pointer', ('NOT READY', RED)))
        if IS_WINDOWS:
            try:
                init_audio_thread()
                playing, error = browser_audio_state(self.browser)
            except Exception as exc:
                playing, error = None, str(exc)
            finally:
                try:
                    close_audio_thread()
                except Exception:
                    pass
        else:
            playing, error = browser_audio_state(self.browser)
        self.log('AUDIO', f'{self.browser} detected_active={playing} error={error}')
        self.log('DIAG', '===== end snapshot =====')

    def refresh_diagnostics(self):
        threading.Thread(target=self.snapshot_diagnostics, name='EG-Diagnose', daemon=True).start()

    def save_delayed(self):
        self.cancel_arming()
        self.armed = False
        self.verified = False
        self.move_result = 'UNTESTED'
        self.note('INFO', 'Capture: window minimizing. Place the physical pointer on Next within 4 seconds.')
        self.root.iconify()
        self.root.after(4000, self.save_target)

    def save_target(self):
        def worker():
            try:
                screens = screen_layout()
                here = pointer_position()
                monitor = find_screen(*here, screens)
                self.log('TARGET', f'Captured pointer position={here}; monitor={monitor}; layout={screens}')
                if not monitor:
                    raise RuntimeError(f'Captured point {here} outside active screen geometry')
                window = capture_window(self.browser, here)
                record = save_target_record(here, screens, self.browser, window)
                self.target, self.saved_layout = here, record['layout']
                self.target_window = window
                self.verified = False
                self.note('TARGET', f'Saved {here} on {monitor}. Ready to ARM; optional tests are under Testing & Troubleshooting.')
            except (OSError, RuntimeError) as exc:
                self.note('ERROR', 'SAVE FAILED: ' + str(exc))
            finally:
                self.events.put(('restore_window', None))
        threading.Thread(target=worker, name='EG-SaveTarget', daemon=True).start()

    def validate_target(self):
        if self.target is None or self.saved_layout is None:
            raise RuntimeError('No saved target. Use Save Next (4s).')
        screens = screen_layout()
        if layout_key(screens) != self.saved_layout:
            self.verified = False
            raise RuntimeError('Monitor arrangement changed. Save target again.')
        if find_screen(*self.target, screens) is None:
            self.verified = False
            raise RuntimeError('Saved target not within active monitors.')
        return screens

    def test_move(self):
        self.armed = False
        self.start_action(click=False)

    def test_click(self):
        self.armed = False
        self.start_action(click=True)

    def start_action(self, click):
        if self.action_lock.locked():
            self.note('WARN', 'Another pointer operation is running.')
            return
        self.root.iconify()
        def worker():
            try:
                time.sleep(.35)
                self.execute_action(click=click, source='Manual')
            finally:
                self.events.put(('restore_window', None))
        threading.Thread(target=worker, name='EG-ManualClick', daemon=True).start()

    def execute_action(self, click, source):
        if not self.action_lock.acquire(blocking=False):
            self.log('WARN', 'Action busy; skipped')
            return False
        try:
            screens = self.validate_target()
            target = self.target
            window = self.target_window
            browser = self.browser
            target_screen = find_screen(*target, screens)
            before = pointer_position()
            before_screen = find_screen(*before, screens)
            self.log('POINTER', f'{source} action={"CLICK" if click else "MOVE ONLY"}; '
                     f'before={before} on={before_screen}; target={target} on={target_screen}')
            self.log('POINTER', f'Global target {target}; backend={"Win32" if IS_WINDOWS else "waytool"}.')
            # Take a snapshot so a GUI change cannot alter an in-flight click.
            settings = dict(self.reliability)
            tolerance = settings['tolerance_px']
            extra = settings['retry_count'] if settings['retries_enabled'] else 0
            settle = settings['settle_ms'] / 1000
            self.log('SETTINGS', f'Action policy retries={extra}, tolerance={tolerance}px, settle={settings["settle_ms"]}ms')
            for attempt in range(1, extra + 2):
                if source == 'Audio' and not self.armed:
                    self.log('INFO', 'Disarmed during positioning; cancelled.')
                    return False
                # No click until the current actual position has been checked.
                move_to(target, trace=self.log)
                time.sleep(settle)
                actual = pointer_position()
                actual_screen = find_screen(*actual, screens)
                delta = (target[0] - actual[0], target[1] - actual[1])
                self.log('POINTER', f'AFTER MOVE attempt={attempt}/{extra + 1} '
                         f'actual={actual} on={actual_screen}; expected={target} '
                         f'on={target_screen}; delta={delta}')
                if actual_screen == target_screen and max(abs(delta[0]), abs(delta[1])) <= tolerance:
                    break
                if attempt <= extra:
                    self.log('RETRY', f'Position outside {tolerance}px tolerance; retrying movement.')
            else:
                self.verified = False
                self.move_result = 'FAILED'
                raise RuntimeError(f'Pointer landed at {actual} on {actual_screen}; '
                                   f'expected {target} on {target_screen}, delta={delta}. NO CLICK.')
            verify_window(window, browser, target, tolerance)
            if not click:
                self.verified = True
                self.move_result = 'VERIFIED'
                self.note('SUCCESS', f'Move Only VERIFIED at {actual} on {target_screen}.')
                return True
            # Cross-check before sending a click; never click at an unverified location.
            latest = pointer_position()
            if (find_screen(*latest, screens) != target_screen or
                    max(abs(latest[0]-target[0]), abs(latest[1]-target[1])) > tolerance):
                self.verified = False
                raise RuntimeError('Pointer changed before click; cancelled')
            if source == 'Audio' and not self.armed:
                self.log('INFO', 'Disarmed before click; cancelled.')
                return False
            verify_window(window, browser, target, tolerance)
            if source == 'Audio' and not self.armed:
                return False
            self.log('CLICK', f'Sending click at {target}; pre-click pointer={latest}.')
            click_at(target, trace=self.log)
            self.click_count += 1
            time.sleep(settle)
            post = pointer_position()
            self.log('CLICK', f'Click command returned success. Post-click pointer={post}; '
                     'Note: cannot independently confirm website navigation.')
            self.note('SUCCESS', f'Click command sent at {target}; count={self.click_count}.')
            # Keep the original conservative behavior: no fighting manual input.
            # A settling interval helps when KWin reports transient coordinates.
            if max(abs(post[0]-target[0]), abs(post[1]-target[1])) <= tolerance:
                if find_screen(*before, screens):
                    try:
                        move_to(before, trace=self.log)
                        back = pointer_position()
                        self.log('POINTER', f'Pointer restore requested={before}; actual={back}')
                        # Retrying restoration is only safe if the cursor is still
                        # at the click target; never chase an actively used pointer.
                        for return_attempt in range(extra):
                            if max(abs(back[0]-before[0]), abs(back[1]-before[1])) <= tolerance:
                                break
                            if max(abs(back[0]-target[0]), abs(back[1]-target[1])) > tolerance:
                                self.log('WARN', 'Return not at original or click target; manual movement possible; no retry.')
                                break
                            self.log('RETRY', f'Restore retry {return_attempt+1}/{extra}; cursor stayed at target.')
                            move_to(before, trace=self.log)
                            time.sleep(settle)
                            back = pointer_position()
                            self.log('POINTER', f'Pointer restore retry actual={back}; expected={before}')
                    except (RuntimeError, OSError) as exc:
                        self.log('WARN', f'Restore failed: {exc}')
            else:
                self.log('WARN', 'Pointer not at target after click, so automatic restore was skipped.')
            return True
        except (OSError, RuntimeError) as exc:
            self.verified = False
            self.armed = False
            self.note('ERROR', 'STOPPED / NO FURTHER CLICKS: ' + str(exc))
            if source == 'Audio':
                self.events.put(('restore_window', None))
            return False
        finally:
            self.action_lock.release()

    def cancel_arming(self):
        self.arming = False
        self.arm_generation = getattr(self, 'arm_generation', 0) + 1

    def toggle_arm(self):
        if self.armed or self.arming:
            self.armed = False
            self.cancel_arming()
            self.note('INFO', 'DISARMED. Automatic clicking paused.')
            return
        self.arming = True
        self.arm_generation += 1
        generation = self.arm_generation
        browser, target, window = self.browser, self.target, self.target_window
        self.note('INFO', 'Checking target and audio. Press Cancel Arm to cancel.')
        def worker():
            error = None
            try:
                self.validate_target()
                if not isinstance(window, dict):
                    raise RuntimeError('The last capture did not save a browser identity. Select the browser, then use Save Next again. Open Logs for capture errors.')
                if self.audio is None:
                    playing, failure = browser_audio_state(browser)
                    if playing is None:
                        raise RuntimeError(f'{browser} audio is unavailable: {failure or self.last_audio_error or "no audio response"}')
            except Exception as exc:
                error = str(exc)
            self.events.put(('arm_result', (generation, browser, target, window, error)))
        threading.Thread(target=worker, name='EG-ArmCheck', daemon=True).start()

    def finish_arming(self, result):
        generation, browser, target, window, error = result
        if not self.arming or generation != self.arm_generation:
            return
        self.arming = False
        if browser != self.browser or target != self.target or window != self.target_window:
            error = 'Target or browser changed during checks. Press Arm again.'
        if error:
            self.armed = False
            self.note('ERROR', 'Cannot arm: ' + error)
            messagebox.showerror('Cannot arm EG-Clicker', error, parent=self.root)
            return
        self.armed = True
        self.note('INFO', f'ARMED. Monitoring {self.browser} for audio stop; target={self.target}.')
        self.root.after(450, lambda: self.root.iconify() if self.armed else None)

    def change_browser(self, browser):
        if browser not in BROWSERS or browser == self.browser:
            return
        self.armed = False
        self.cancel_arming()
        self.browser = browser
        if not matches_saved_browser(self.target_window, browser):
            self.target_window = None
        self.audio = None
        self.last_audio_state = 'CHECKING'
        self.last_audio_error = ''
        try:
            save_browser_choice(browser)
        except OSError as exc:
            self.note('WARN', 'Unable to save browser selection: ' + str(exc))
        instruction = 'Re-arm to monitor.' if self.target_window else 'Save Next again before arming.'
        self.note('INFO', f'Browser changed to {browser}; clicker DISARMED. {instruction}')
        if IS_WINDOWS:
            self.log('WARN', 'Windows audio: selected-browser active session AND default-output peak; other applications may affect peak detection.')

    def audio_watcher(self):
        try:
            init_audio_thread()
        except Exception as exc:
            self.note('ERROR', f'Audio initialization failed: {exc}')
            return
        was_playing, silent_since, current_browser = False, None, self.browser
        try:
            while self.running:
                browser = self.browser
                if browser != current_browser:
                    current_browser, was_playing, silent_since = browser, False, None
                playing, error = browser_audio_state(browser)
                self.audio = playing
                state = 'UNAVAILABLE' if playing is None else ('PLAYING' if playing else 'SILENT')
                if state != self.last_audio_state:
                    self.log('AUDIO', f'{browser}: {self.last_audio_state} -> {state}')
                    self.last_audio_state = state
                if error and error != self.last_audio_error:
                    self.note('WARN', f'Audio error ({browser}): {error}')
                self.last_audio_error = error or ''
                if not self.armed or playing is None:
                    was_playing, silent_since = False, None
                elif playing:
                    was_playing, silent_since = True, None
                elif was_playing:
                    if silent_since is None:
                        silent_since = time.monotonic()
                        self.log('AUDIO', f'{browser} silent; waiting 2 seconds.')
                    elif time.monotonic() - silent_since >= 2.0:
                        check, failure = browser_audio_state(browser)
                        self.log('AUDIO', f'Confirmation {browser}: active={check}, error={failure}')
                        if self.armed and self.browser == browser and check is False:
                            self.execute_action(click=True, source='Audio')
                        was_playing, silent_since = False, None
                time.sleep(.5)
        finally:
            close_audio_thread()

    def show_logs(self):
        if self.log_window is not None and self.log_window.winfo_exists():
            self.log_window.deiconify()
            self.log_window.lift()
            return
        window = tk.Toplevel(self.root)
        self.log_window = window
        window.title('EG-Clicker Logs')
        window.geometry('850x500')
        tk.Label(window, text='Saved log: ' + str(self.filelog.path), anchor='w').pack(fill='x', padx=8, pady=6)
        self.log_viewer = scrolledtext.ScrolledText(window, wrap='word', font=('DejaVu Sans Mono', 9))
        self.log_viewer.pack(fill='both', expand=True, padx=8)
        bar = tk.Frame(window)
        bar.pack(fill='x', padx=8, pady=8)
        tk.Button(bar, text='Copy All Logs', command=self.copy_logs).pack(side='left')
        tk.Button(bar, text='Save Log As…', command=self.save_logs_as).pack(side='left', padx=8)
        self.update_log_window()

    def update_log_window(self):
        if self.log_window is not None and self.log_window.winfo_exists():
            self.log_viewer.configure(state='normal')
            self.log_viewer.delete('1.0', 'end')
            self.log_viewer.insert('end', '\n'.join(self.history))
            self.log_viewer.see('end')
            self.log_viewer.configure(state='disabled')

    def callback_error(self, exception_type, value, tb):
        import traceback
        self.armed = False
        self.cancel_arming()
        details = ''.join(traceback.format_exception(exception_type, value, tb))
        if details == self.last_callback_error:
            return
        self.last_callback_error = details
        self.log('ERROR', 'GUI callback failed: ' + details)
        self.note_message = 'An interface error stopped automation. Open Logs for details.'
        self.note_bad = True
        self.show_logs()
        messagebox.showerror('EG-Clicker interface error', str(value) + '\nAutomation stopped. Details are in Open Logs.', parent=self.root)

    def copy_logs(self):
        lines = '\n'.join(self.history) + '\n'
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(lines)
            self.root.update()  # lets Tk own the clipboard after the app loses focus
            self.note('INFO', f'Copied {len(self.history)} log entries to clipboard.')
        except tk.TclError as exc:
            self.note('ERROR', 'Clipboard error: ' + str(exc))

    def save_logs_as(self):
        path = filedialog.asksaveasfilename(parent=self.root, defaultextension='.log',
                    filetypes=[('Log files','*.log'), ('Text files', '*.txt'), ('All files','*.*')],
                    initialfile='EG-Clicker-diagnostics.log', title='Save EG-Clicker log')
        if not path:
            return
        try:
            Path(path).write_text('\n'.join(self.history) + '\n', encoding='utf-8')
            self.note('INFO', 'Exported log to: ' + path)
        except OSError as exc:
            self.note('ERROR', 'Export log failed: ' + str(exc))

    def clear_log_view(self):
        self.history.clear()
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.configure(state='disabled')
        self.note('INFO', 'Visible log cleared; automatic disk log retained.')

    def refresh(self):
        try:
            self.refresh_once()
        except Exception:
            self.callback_error(*sys.exc_info())
        finally:
            if self.running:
                self.root.after(150, self.refresh)

    def refresh_once(self):
        pending_logs = []
        while True:
            try:
                kind, val = self.events.get_nowait()
            except queue.Empty:
                break
            if kind == 'arm_result':
                self.finish_arming(val)
            elif kind == 'log':
                for line in val.split('\n'):
                    self.history.append(line)
                    pending_logs.append(line)
            elif kind == 'note':
                level, message = val
                self.note_message = message
                self.note_bad = level == 'ERROR'
            elif kind == 'pointer':
                label, color = val
                self.pointer_label.configure(text=label, fg=color)
            elif kind == 'restore_window':
                self.root.deiconify()
                self.root.lift()
            elif kind == 'displays':
                self.footer.configure(text='Displays: ' + val + '  •  Wrong position = NO CLICK')
        if pending_logs:
            self.log_text.configure(state='normal')
            self.log_text.insert('end', '\n'.join(pending_logs) + '\n')
            # Prevent unbounded Tk text growth; log file is preserved.
            rowcount = int(self.log_text.index('end-1c').split('.')[0])
            if rowcount > 1900:
                self.log_text.delete('1.0', f'{rowcount-1500}.0')
            self.log_text.see('end')
            self.log_text.configure(state='disabled')
        if pending_logs:
            self.update_log_window()
        self.arm_button.configure(text='Cancel Arm' if self.arming else 'Arm / Disarm')
        self.note_label.configure(text=self.note_message, fg=RED if self.note_bad else MUTED)
        self.target_label.configure(text=(f'{self.target[0]}, {self.target[1]}' if self.target else 'NOT SAVED'),
                                    fg=GREEN if self.verified else YELLOW)
        state = self.audio
        self.audio_label.configure(text='PLAYING' if state else ('SILENT' if state is False else 'UNAVAILABLE'),
                                   fg=GREEN if state is True else (YELLOW if state is False else RED))
        self.arm_label.configure(text=('ARMED  •  MONITORING' if self.armed else
                                       ('DISARMED  •  TARGET READY' if self.target else 'DISARMED  •  SAVE A TARGET')),
                                 fg=GREEN if self.armed else (YELLOW if self.target else RED))
        self.count_label.configure(text=f'Click commands sent: {self.click_count}  |  Move: {self.move_result}')

    def close(self):
        self.cancel_arming()
        self.armed = False
        self.running = False
        self.log('INFO', 'EG-Clicker closed.')
        self.root.destroy()


def diagnose_cli():
    print(f'EG-Clicker {VERSION} — Diagnostic report (NO pointer movement)')
    print('Platform:', sys.platform)
    print('Selected browser:', load_browser())
    print('Target:', load_target()[0])
    try:
        for line in (('pointer', pointer_position()), ('monitors', screen_layout()),
                     ('pointer control', pointer_health())):
            print(line[0], ':', line[1])
    except RuntimeError as exc:
        print('ERROR:', exc)
    if IS_WINDOWS:
        print('Windows audio uses active browser session + shared output peak. Other applications may affect detection.')
    else:
        print('Wayland session:', os.environ.get('XDG_SESSION_TYPE', 'unset'))
    print('Log:', LOG_FILE)


if __name__ == '__main__':
    init_desktop()
    if '--diagnose' in sys.argv:
        diagnose_cli()
    else:
        if not IS_WINDOWS and os.geteuid() == 0:
            sys.exit('Run as your normal desktop user, not sudo.')
        if not IS_WINDOWS and os.environ.get('XDG_SESSION_TYPE', '').lower() != 'wayland':
            sys.exit('EG-Clicker Fedora edition requires KDE Wayland.')
        root = tk.Tk()
        App(root)
        root.mainloop()
