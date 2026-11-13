"""EG desktop styling and layout. Uses standard Tk/ttk; no extra GUI packages."""
import tkinter as tk
from tkinter import ttk, font as tkfont
import webbrowser
import re

NAVY = '#0b1120'
NAVY2 = '#121d30'
PANEL = '#19283e'
PANEL2 = '#203552'
BLUE = '#438dff'
SKY = '#8ec1ff'
WHITE = '#edf4ff'
MUTED = '#95a9c5'
YELLOW = '#ffd185'
GREEN = '#65deb0'
RED = '#ff8f9d'
LINE = '#26374f'


def setup_style(root):
    families = tkfont.families(root)
    family = next((f for f in ('Segoe UI', 'Inter', 'Noto Sans', 'DejaVu Sans') if f in families), 'Sans')
    root.option_add('*Font', (family, 10))
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('EG.TButton', font=(family, 10), padding=(14, 10), borderwidth=0,
                    relief='flat', background=PANEL2, foreground=WHITE, focusthickness=0)
    style.map('EG.TButton', background=[('active', '#2c4568'), ('pressed', '#162b46')])
    style.configure('Primary.EG.TButton', background=BLUE, foreground='#071329', font=(family, 10, 'bold'))
    style.map('Primary.EG.TButton', background=[('active', '#73acff'), ('pressed', '#3075dd')])
    style.configure('Small.EG.TButton', padding=(11, 7), font=(family, 9))
    style.configure('EG.TCombobox', fieldbackground=PANEL, background=PANEL2,
                    foreground=WHITE, arrowcolor=MUTED, bordercolor=LINE, padding=9,
                    selectbackground=PANEL2, selectforeground=WHITE, lightcolor=LINE, darkcolor=LINE)
    style.map('EG.TCombobox', fieldbackground=[('readonly', PANEL)], foreground=[('readonly', WHITE)],
              bordercolor=[('focus', BLUE), ('!focus', LINE)], lightcolor=[('!focus', LINE)], darkcolor=[('!focus', LINE)])
    style.configure('EG.TCheckbutton', background=NAVY2, foreground=WHITE,
                    font=(family, 10), padding=(0, 6), indicatorbackground=PANEL2, indicatorforeground=WHITE)
    style.map('EG.TCheckbutton', background=[('active', NAVY2)], foreground=[('active', WHITE)],
              indicatorbackground=[('selected', BLUE), ('!selected', PANEL2)])
    style.configure('EG.Vertical.TScrollbar', background=PANEL2, troughcolor=NAVY2,
                    borderwidth=0, arrowsize=10, bordercolor=NAVY2, lightcolor=NAVY2, darkcolor=NAVY2, arrowcolor=MUTED)
    style.map('EG.Vertical.TScrollbar', background=[('pressed', BLUE), ('active', PANEL2), ('!active', PANEL2)],
              bordercolor=[('!disabled', NAVY2)], lightcolor=[('!disabled', NAVY2)], darkcolor=[('!disabled', NAVY2)])
    return family


def label(parent, text, size=10, color=WHITE, bold=False, **kwargs):
    return tk.Label(parent, text=text, bg=parent.cget('bg'), fg=color,
                    font=(parent.winfo_toplevel().eg_font, size, 'bold' if bold else 'normal'), **kwargs)


def button(parent, text, command, primary=False, small=False):
    return ttk.Button(parent, text=text, command=command,
                      style='Primary.EG.TButton' if primary else ('Small.EG.TButton' if small else 'EG.TButton'))


def card(parent, **kwargs):
    return tk.Frame(parent, bg=NAVY2, highlightbackground=LINE, highlightthickness=1, **kwargs)


def build_ui(a, version, logo_data):
    root = a.root
    root.eg_font = setup_style(root)
    root.configure(bg=NAVY)
    root.geometry(f'1060x{max(650, min(760, root.winfo_screenheight()-100))}')
    root.minsize(880, 640)
    a.settings_window = None
    header = tk.Frame(root, bg=NAVY, padx=24, pady=18)
    header.pack(fill='x')
    try:
        a.logo = tk.PhotoImage(data=logo_data)
        a.header_logo = a.logo.subsample(2, 2)
        tk.Label(header, image=a.header_logo, bg=NAVY).pack(side='left', padx=(0, 14))
        root.iconphoto(True, a.logo)
    except tk.TclError:
        pass
    identity = tk.Frame(header, bg=NAVY)
    identity.pack(side='left')
    label(identity, 'EG-Clicker', 25, bold=True).pack(anchor='w')
    brand = label(identity, 'EHRHART GROUP LLC  /  AUDIO AUTOMATION', 8, MUTED, cursor='hand2')
    brand.pack(anchor='w', pady=(2, 0))
    brand.bind('<Button-1>', lambda _event: webbrowser.open('https://ehrhartgroup.us'))
    button(header, 'Settings', a.toggle_reliability).pack(side='right')
    button(header, 'Open Logs', a.show_logs).pack(side='right', padx=8)
    label(header, f'v{version}', 9, MUTED).pack(side='right', padx=12)

    status = tk.Frame(root, bg=NAVY)
    status.pack(fill='x', padx=24, pady=(0, 16))
    values = []
    for i, title in enumerate(('SAVED TARGET', 'BROWSER AUDIO', 'POINTER')):
        status.columnconfigure(i, weight=1, uniform='status')
        tile = card(status, padx=16, pady=12)
        tile.grid(row=0, column=i, sticky='nsew', padx=(0 if i == 0 else 6, 0 if i == 2 else 6))
        label(tile, title, 8, MUTED, True).pack(anchor='w')
        value = label(tile, 'Checking…', 16, SKY, True)
        value.pack(anchor='w', pady=(5, 0))
        values.append(value)
    a.target_label, a.audio_label, a.pointer_label = values

    body = tk.Frame(root, bg=NAVY)
    body.pack(fill='both', expand=True, padx=24)
    body.columnconfigure(0, weight=4, minsize=340)
    body.columnconfigure(1, weight=6, minsize=400)
    body.rowconfigure(0, weight=1)
    control = card(body)
    control.grid(row=0, column=0, sticky='nsew', padx=(0, 14))
    canvas = tk.Canvas(control, bg=NAVY2, highlightthickness=0, borderwidth=0)
    scrollbar = ttk.Scrollbar(control, orient='vertical', command=canvas.yview, style='EG.Vertical.TScrollbar')
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side='right', fill='y')
    canvas.pack(side='left', fill='both', expand=True)
    inner = tk.Frame(canvas, bg=NAVY2, padx=18, pady=18)
    item = canvas.create_window((0, 0), window=inner, anchor='nw')
    inner.bind('<Configure>', lambda _event: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.bind('<Configure>', lambda event: canvas.itemconfigure(item, width=event.width))
    label(inner, 'Your automation', 15, bold=True).pack(anchor='w')
    label(inner, 'Browser audio ends. Your saved target gets a click.', 9, MUTED,
          wraplength=310, justify='left').pack(anchor='w', pady=(5, 12))
    a.destination_label = label(inner, '', 9, SKY, True)
    a.destination_label.pack(anchor='w', pady=(0, 14))
    label(inner, 'Listen for audio in', 9, MUTED).pack(anchor='w', pady=(0, 5))
    from eg_platform import BROWSERS
    browser = ttk.Combobox(inner, textvariable=a.browser_var, values=BROWSERS, state='readonly', style='EG.TCombobox')
    browser.pack(fill='x', pady=(0, 14))
    browser.bind('<<ComboboxSelected>>', lambda _event: a.change_browser(a.browser_var.get()))
    label(inner, 'Website to launch', 9, MUTED).pack(anchor='w', pady=(0, 5))
    launch = tk.Frame(inner, bg=NAVY2)
    launch.pack(fill='x', pady=(0, 18))
    entry = tk.Entry(launch, textvariable=a.launch_url_var, bg=PANEL, fg=WHITE,
                     insertbackground=WHITE, relief='flat', highlightbackground=LINE,
                     highlightcolor=BLUE, highlightthickness=1, width=15)
    entry.pack(side='left', fill='both', expand=True, ipady=9, padx=(0, 8))
    button(launch, 'Launch', a.launch_browser, small=True).pack(side='right', fill='y')
    actions = tk.Frame(inner, bg=NAVY2)
    actions.pack(fill='x')
    actions.columnconfigure((0, 1), weight=1, uniform='action')
    button(actions, 'Save Next · 4s', a.save_delayed).grid(row=0, column=0, sticky='ew', padx=(0, 5))
    a.arm_button = button(actions, 'Arm clicker', a.toggle_arm, primary=True)
    a.arm_button.grid(row=0, column=1, sticky='ew', padx=(5, 0))
    a.arm_label = label(inner, 'DISARMED', 9, YELLOW, True)
    a.arm_label.pack(anchor='w', pady=(13, 5))
    a.count_label = label(inner, '0 clicks', 9, MUTED)
    a.count_label.pack(anchor='w', pady=(0, 15))
    a.testing_button = button(inner, 'Pointer tests  ▾', a.toggle_testing, small=True)
    a.testing_button.pack(anchor='w')
    a.testing_open = False
    a.testing_frame = tk.Frame(inner, bg=NAVY2)
    for text, callback in (('Move only', a.test_move), ('Test click', a.test_click), ('Check setup', a.refresh_diagnostics)):
        button(a.testing_frame, text, callback, small=True).pack(side='left', padx=(0, 5), pady=8)
    a.note_label = label(inner, '', 9, MUTED, wraplength=300, justify='left', anchor='w')
    a.note_label.pack(fill='x', pady=(14, 0))

    activity = card(body, padx=16, pady=16)
    activity.grid(row=0, column=1, sticky='nsew')
    toolbar = tk.Frame(activity, bg=NAVY2)
    toolbar.pack(fill='x', pady=(0, 12))
    label(toolbar, 'Activity', 15, bold=True).pack(side='left')
    button(toolbar, 'Export', a.save_logs_as, small=True).pack(side='right')
    button(toolbar, 'Copy', a.copy_logs, small=True).pack(side='right', padx=7)
    label(activity, 'Live updates · saved on this device', 9, MUTED).pack(anchor='w', pady=(0, 10))
    a.log_text = text_area(activity, bg='#0c1423', fg='#bccce3',
                insertbackground=WHITE, relief='flat', borderwidth=0, highlightthickness=0,
                font=('DejaVu Sans Mono', 9), wrap='word', padx=12, pady=12, height=10, state='disabled')
    a.log_text.tag_configure('error', foreground=RED)
    a.log_text.tag_configure('success', foreground=GREEN)
    a.log_text.tag_configure('info', foreground='#bccce3')
    a.diagnostics_open = True
    a.diagnostics_frame = activity
    a.footer = tk.Label(root, bg=NAVY, fg=MUTED, font=(root.eg_font, 8), anchor='w',
                         text='Logs saved automatically · Open Logs for the file location', wraplength=1000, justify='left')
    a.footer.pack(fill='x', padx=25, pady=(10, 12))


def open_settings(a):
    if a.settings_window is not None and a.settings_window.winfo_exists():
        a.settings_window.lift()
        return
    a.require_window_var.set(a.reliability.get('require_browser_window', False))
    a.retry_enabled_var.set(a.reliability['retries_enabled'])
    a.retry_count_var.set(str(a.reliability['retry_count']))
    a.tolerance_var.set(str(a.reliability['tolerance_px']))
    a.settle_var.set(str(a.reliability['settle_ms']))
    window = tk.Toplevel(a.root)
    a.settings_window = window
    window.eg_font = a.root.eg_font
    window.title('EG-Clicker · Settings')
    window.configure(bg=NAVY)
    window.geometry('600x660')
    window.minsize(550, 560)
    heading = tk.Frame(window, bg=NAVY, padx=24, pady=20)
    heading.pack(fill='x')
    label(heading, 'Clicker settings', 21, bold=True).pack(anchor='w')
    label(heading, 'Choose where to click and how the pointer settles.', 10, MUTED).pack(anchor='w', pady=(5, 0))
    panel = card(window, padx=20, pady=18)
    # Pack actions at the bottom first so they remain visible on smaller displays.
    controls = tk.Frame(window, bg=NAVY)
    controls.pack(side='bottom', fill='x', padx=24, pady=(0, 20))
    panel.pack(fill='both', expand=True, padx=24, pady=(0, 16))
    label(panel, 'CLICK DESTINATION', 9, SKY, True).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 7))
    ttk.Checkbutton(panel, text='Require the captured browser window', variable=a.require_window_var,
                    style='EG.TCheckbutton').grid(row=1, column=0, columnspan=2, sticky='w')
    label(panel, 'Off: click any saved desktop location, regardless of focus.\nOn: require the same active, uncovered browser window.',
          9, MUTED, justify='left', wraplength=485).grid(row=2, column=0, columnspan=2, sticky='w', pady=(2, 18))
    label(panel, 'POINTER RELIABILITY', 9, SKY, True).grid(row=3, column=0, columnspan=2, sticky='w', pady=(0, 7))
    ttk.Checkbutton(panel, text='Retry movement if positioning misses', variable=a.retry_enabled_var,
                    style='EG.TCheckbutton').grid(row=4, column=0, columnspan=2, sticky='w', pady=(0, 10))
    fields = [('Extra retries', a.retry_count_var, tuple(str(n) for n in range(6))),
              ('Position tolerance · pixels', a.tolerance_var, tuple(str(n) for n in range(13))),
              ('Settle delay · milliseconds', a.settle_var, ('100','150','200','250','300','400','500','700'))]
    for i, (title, variable, values) in enumerate(fields, start=5):
        label(panel, title, 10).grid(row=i, column=0, sticky='w', pady=7)
        ttk.Combobox(panel, textvariable=variable, values=values, state='readonly', width=9,
                      style='EG.TCombobox').grid(row=i, column=1, sticky='e', pady=7)
    panel.columnconfigure(0, weight=1)
    label(panel, 'Settings take effect when saved. Saving pauses monitoring.', 9, MUTED,
          wraplength=470, justify='left').grid(row=8, column=0, columnspan=2, sticky='w', pady=(17, 0))
    button(controls, 'Restore defaults', a.reset_reliability).pack(side='left')
    button(controls, 'Save settings', a.apply_reliability, primary=True).pack(side='right')
    button(controls, 'Close', window.destroy).pack(side='right', padx=8)


def text_area(parent, outer_padding=0, **options):
    frame = tk.Frame(parent, bg=NAVY2)
    frame.pack(fill='both', expand=True, padx=outer_padding)
    scroll = ttk.Scrollbar(frame, orient='vertical', style='EG.Vertical.TScrollbar')
    text = tk.Text(frame, yscrollcommand=scroll.set, **options)
    scroll.configure(command=text.yview)
    scroll.pack(side='right', fill='y')
    text.pack(side='left', fill='both', expand=True)
    return text


def open_log_window(a):
    if a.log_window is not None and a.log_window.winfo_exists():
        a.log_window.deiconify()
        a.log_window.lift()
        return
    window = tk.Toplevel(a.root)
    a.log_window = window
    window.eg_font = a.root.eg_font
    window.title('EG-Clicker · Activity log')
    window.geometry('920x560')
    window.configure(bg=NAVY)
    bar = tk.Frame(window, bg=NAVY, padx=20, pady=16)
    bar.pack(fill='x')
    label(bar, 'Activity log', 19, bold=True).pack(side='left')
    button(bar, 'Export', a.save_logs_as, small=True).pack(side='right')
    button(bar, 'Copy all', a.copy_logs, small=True).pack(side='right', padx=8)
    a.log_viewer = text_area(window, outer_padding=20, bg=NAVY2, fg=WHITE,
                    relief='flat', borderwidth=0, padx=15, pady=15,
                    font=('DejaVu Sans Mono', 9), wrap='word')
    label(window, 'Saved on this device: ' + str(a.filelog.path), 9, MUTED,
          wraplength=870, justify='left').pack(anchor='w', padx=20, pady=12)
    a.update_log_window()


def format_activity_line(line):
    match = re.match(r'^\d{4}-\d{2}-\d{2} (\d{2}:\d{2}:\d{2})\.\d+[+-]\d{4} \[([^]]+)\] (.*)$', line)
    if match:
        return f'{match[1]}  {match[2].strip():<8} {match[3]}'
    return line
