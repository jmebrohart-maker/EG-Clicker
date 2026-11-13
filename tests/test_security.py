from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import launcher
import window_guard as guard

WINDOW='{01234567-89ab-cdef-0123-456789abcdef}'
OTHER='{11234567-89ab-cdef-0123-456789abcdef}'

def output(window=WINDOW, active=WINDOW, geometry='1920x1080', klass='firefox'):
    return f'x:100 y:100 screen:0 window:{window}\n{window}\n123\n{klass}\nWindow {window}\n  Position: 0,0\n  Geometry: {geometry}\n{active}\n'

class WindowGuardTests(unittest.TestCase):
    def setUp(self):
        for target, kwargs in [('run_cmd', {'return_value':output()}),
                               ('process_identity', {'return_value':('firefox', '10000')}),
                               ('IS_WINDOWS', {'new':False})]:
            patcher=patch.object(guard,target,**kwargs)
            value=patcher.start();self.addCleanup(patcher.stop)
            if target=='run_cmd':self.command=value
            if target=='process_identity':self.process=value
        self.saved=guard.capture_window('Firefox',(100,100))

    def test_any_browser_preserves_compatible_binding(self):
        self.assertTrue(guard.matches_saved_browser(self.saved, 'Any Browser'))
        self.assertTrue(guard.matches_saved_browser(self.saved, 'Firefox'))
        self.assertFalse(guard.matches_saved_browser(self.saved, 'Chrome'))

    def test_same_window_accepted(self):
        self.assertTrue(guard.verify_window(self.saved,'Firefox',(100,100),0))

    def test_firefox_wayland_app_id_is_not_treated_as_a_process_name(self):
        self.command.return_value=output(klass='org.mozilla.firefox')
        saved=guard.capture_window('Firefox',(100,100))
        self.assertEqual(saved['class'],'org.mozilla.firefox')
        self.assertTrue(guard.verify_window(saved,'Firefox',(100,100),0))
        self.assertTrue(guard.matches_saved_browser(saved,'Any Browser'))

    def test_foreign_process_with_firefox_class_still_rejected(self):
        self.process.return_value=('chrome','10000')
        with self.assertRaisesRegex(RuntimeError, 'executable='):
            guard.capture_window('Firefox',(100,100))

    def test_captured_window_class_changes_still_rejected(self):
        self.command.return_value=output(klass='org.mozilla.firefox')
        with self.assertRaises(RuntimeError):guard.verify_window(self.saved,'Firefox',(100,100),0)

    def test_covered_window_rejected(self):
        self.command.return_value=output(window=OTHER, active=OTHER)
        with self.assertRaises(RuntimeError):guard.verify_window(self.saved,'Firefox',(100,100),4)

    def test_inactive_browser_rejected(self):
        self.command.return_value=output(active=OTHER)
        with self.assertRaises(RuntimeError):guard.verify_window(self.saved,'Firefox',(100,100),4)

    def test_resized_browser_rejected(self):
        self.command.return_value=output(geometry='900x600')
        with self.assertRaises(RuntimeError):guard.verify_window(self.saved,'Firefox',(100,100),4)

    def test_restarted_process_rejected(self):
        self.process.return_value=('firefox','20000')
        with self.assertRaises(RuntimeError):guard.verify_window(self.saved,'Firefox',(100,100),4)

    def test_spoofed_browser_class_does_not_bypass_process_check(self):
        self.process.return_value=('unrelated-app','10000')
        with self.assertRaises(RuntimeError):guard.verify_window(self.saved,'Firefox',(100,100),4)

    def test_legacy_target_requires_recapture(self):
        with self.assertRaises(RuntimeError):guard.verify_window(None,'Firefox',(100,100),4)

    def test_fractional_scaled_desktop_coordinates_are_parsed(self):
        record=guard.parse_snapshot(output().replace('x:100 y:100','x:100.5 y:100.25').replace('Position: 0,0','Position: -0.5,0.25'))
        self.assertEqual(record['pointer'],[100,100])
        self.assertEqual(record['geometry'][:2],[-0.5,0.25])

    def test_invalid_snapshot_rejected(self):
        for value in ('', output().replace('123','0'), output().replace('Geometry: 1920x1080','Geometry: 0x0')):
            with self.assertRaises(RuntimeError):guard.parse_snapshot(value)

    def test_pointer_shift_during_capture_rejected(self):
        with self.assertRaises(RuntimeError):guard.capture_window('Firefox',(200,200))

class BrowserLookupTests(unittest.TestCase):
    @unittest.skipIf(os.name=='nt','Fedora executable policy')
    def test_writable_path_executable_is_never_selected(self):
        with tempfile.TemporaryDirectory() as temp:
            fake=Path(temp)/'firefox';fake.write_text('#!/bin/sh\nexit 0\n');fake.chmod(0o700)
            with patch.dict(os.environ,{'PATH':temp}):
                try: chosen=launcher.browser_executable('Firefox')
                except RuntimeError: chosen=None
            self.assertNotEqual(chosen,str(fake))

    def test_default_browser_uses_trusted_opener_and_sanitized_path(self):
        with patch.object(launcher.os,'name','posix'), patch.object(launcher,'trusted_linux_executable',return_value='/usr/bin/xdg-open'), patch.object(launcher.subprocess,'Popen') as spawn:
            spawn.return_value.wait.return_value=0
            launcher.launch_browser('Any Browser','https://example.com')
            self.assertEqual(spawn.call_args.args[0],['/usr/bin/xdg-open','https://example.com'])
            self.assertEqual(spawn.call_args.kwargs['env']['PATH'],'/usr/bin:/bin')

if __name__=='__main__':unittest.main()
