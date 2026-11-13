"""Fail closed unless a click still belongs to the captured KDE browser window."""
import os
from pathlib import Path
import re
from eg_platform import IS_WINDOWS, _matches, run_cmd

SNAPSHOT_ARGS = ('kdotool', 'getmouselocation', 'getwindowid', 'getwindowpid',
                 'getwindowclassname', 'getwindowgeometry', 'getactivewindow', 'getwindowid')


def parse_snapshot(output):
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if len(lines) != 8:
        raise RuntimeError('Cannot verify the browser window: unexpected kdotool output.')
    point = re.fullmatch(r'x:(-?\d+(?:\.\d+)?) y:(-?\d+(?:\.\d+)?) screen:-?\d+ window:(\{[0-9a-fA-F-]{36}\})', lines[0])
    position = re.fullmatch(r'Position: (-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)', lines[5])
    size = re.fullmatch(r'Geometry: (\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)', lines[6])
    if (not point or not position or not size or lines[1] != point[3]
            or lines[4] != 'Window ' + lines[1] or not lines[2].isdigit()):
        raise RuntimeError('Cannot verify the browser window: invalid kdotool snapshot.')
    geometry = [float(position[1]), float(position[2]), float(size[1]), float(size[2])]
    if min(geometry[2:]) <= 0 or int(lines[2]) <= 0:
        raise RuntimeError('Cannot verify the browser window geometry or process.')
    return {'id': lines[1], 'pid': int(lines[2]), 'class': lines[3].lower(),
            'geometry': geometry, 'active': lines[7],
            'pointer': [int(float(point[1])), int(float(point[2]))]}


def process_identity(pid):
    try:
        executable = Path(f'/proc/{pid}/exe')
        image = os.readlink(executable)
        info = executable.stat()
        # The process must execute a protected, root-owned browser binary.
        if info.st_uid != 0 or info.st_mode & 0o022 or image.endswith(' (deleted)'):
            raise RuntimeError('Browser executable is not a protected system installation.')
        # comm may contain spaces or parentheses; fields after the final ')' start at field 3.
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        return Path(image).name.lower(), fields[19]
    except (OSError, IndexError) as exc:
        raise RuntimeError('Cannot verify the browser process; capture the target again.') from exc


def snapshot(browser):
    if IS_WINDOWS:
        raise RuntimeError('Secure window verification currently requires KDE Wayland; clicks disabled on Windows.')
    record = parse_snapshot(run_cmd(*SNAPSHOT_ARGS, timeout=12, quiet=True))
    image, started = process_identity(record['pid'])
    if not _matches(image, browser, 'linux') or not _matches(record['class'], browser, 'linux'):
        raise RuntimeError('The pointer is not over the selected browser. Save Next again on its window.')
    if record['active'] != record['id']:
        raise RuntimeError('The captured browser must be the active window. No click was sent.')
    record.update(image=image, started=started)
    return record


def capture_window(browser, point):
    record = snapshot(browser)
    if record['pointer'] != list(point):
        raise RuntimeError('Pointer moved during capture. Save Next again.')
    x, y, w, h = record['geometry']
    if not (x <= point[0] < x+w and y <= point[1] < y+h):
        raise RuntimeError('Target is outside the browser window.')
    return {key: record[key] for key in ('id', 'pid', 'class', 'geometry', 'image', 'started')}


def verify_window(saved, browser, point, tolerance):
    if not isinstance(saved, dict) or any(key not in saved for key in ('id', 'pid', 'class', 'geometry', 'image', 'started')):
        raise RuntimeError('Save Next again to bind this target to its browser window.')
    current = snapshot(browser)
    for key in ('id', 'pid', 'class', 'geometry', 'image', 'started'):
        if current[key] != saved[key]:
            raise RuntimeError('Browser window changed, moved, or was covered. No click; save the target again.')
    if max(abs(current['pointer'][i] - point[i]) for i in (0, 1)) > tolerance:
        raise RuntimeError('Pointer changed during window verification. No click was sent.')
    return True
