"""Optional Windows-only target-window binding. Anywhere mode does not call it."""
from eg_platform import window_snapshot, _matches

KEYS = ('id', 'pid', 'class', 'geometry', 'image', 'started')

def snapshot(browser):
    record = window_snapshot()
    if not _matches(record['image'], browser):
        raise RuntimeError(f'Expected {browser}; target process is {record["image"]}. Select the matching browser or use Anywhere mode.')
    if record['active'] != record['id']:
        raise RuntimeError('Browser-only mode requires the captured browser to be active and uncovered.')
    return record


def capture_window(browser, point):
    record = snapshot(browser)
    if record['pointer'] != list(point):
        raise RuntimeError('Pointer moved during capture; try Save Next again.')
    x,y,w,h = record['geometry']
    if not (x <= point[0] < x+w and y <= point[1] < y+h):
        raise RuntimeError('Target is outside the browser window.')
    return {key:record[key] for key in KEYS}


def verify_window(saved, browser, point, tolerance):
    if not isinstance(saved, dict) or any(key not in saved for key in KEYS):
        raise RuntimeError('Capture the browser target again, or turn off the browser-window restriction.')
    current = snapshot(browser)
    if any(current[key] != saved[key] for key in KEYS):
        raise RuntimeError('Captured browser changed, moved, or was covered. No click was sent.')
    if max(abs(current['pointer'][i]-point[i]) for i in (0,1)) > tolerance:
        raise RuntimeError('Pointer changed during verification. No click was sent.')
    return True


def matches_saved_browser(saved, browser):
    return isinstance(saved, dict) and isinstance(saved.get('image'), str) and _matches(saved['image'], browser)
