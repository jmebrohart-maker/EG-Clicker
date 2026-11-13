import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
spec = importlib.util.spec_from_file_location('app', Path(__file__).resolve().parents[1] / 'EG-Clicker.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
import launcher

class SettingsTests(unittest.TestCase):
    def test_roundtrip_preserves_target_browser_url(self):
        with tempfile.TemporaryDirectory() as d, patch.object(app, 'CONFIG', Path(d)/'config.json'):
            app._secure_atomic_json(app.CONFIG, {'x': -50, 'y': 20, 'browser': 'Firefox'})
            app.save_launch_url('https://example.com/path?q=1')
            app.save_reliability({'retries_enabled': True, 'retry_count': 3, 'tolerance_px': 2, 'settle_ms': 500})
            screens = [{'name': 'screen', 'x': -100, 'y': 0, 'w': 1920, 'h': 1080}]
            app.save_target_record((-50, 20), screens, 'Firefox')
            self.assertEqual(app.load_reliability()['retry_count'], 3)
            record = app.read_config(app.CONFIG)
            self.assertEqual(record['x'], -50)
            self.assertEqual(record['launch_url'], 'https://example.com/path?q=1')
            app.save_browser_choice('Chrome')
            self.assertEqual(app.load_browser(), 'Chrome')

    def test_changing_to_any_browser_preserves_saved_window(self):
        with tempfile.TemporaryDirectory() as d, patch.object(app, 'CONFIG', Path(d)/'config.json'):
            window={'id':'browser', 'image':'firefox', 'class':'firefox'}
            app._secure_atomic_json(app.CONFIG, {'browser':'Firefox', 'target_window':window})
            app.save_browser_choice('Any Browser')
            self.assertEqual(app.read_config()['target_window'],window)
            app.save_browser_choice('Chrome')
            self.assertNotIn('target_window',app.read_config())

    def test_malformed_roots_recover(self):
        with tempfile.TemporaryDirectory() as d, patch.object(app, 'CONFIG', Path(d)/'config.json'):
            for raw in ('[]', 'null', '5', 'invalid'):
                app.CONFIG.write_text(raw)
                self.assertEqual(app.load_browser(), 'Firefox')
                app.save_browser_choice('Edge')
                self.assertEqual(app.load_browser(), 'Edge')

    def test_bounds(self):
        normalized = app.normalize_reliability({'retry_count': 100, 'tolerance_px': -1, 'settle_ms': 'bad'})
        self.assertEqual((normalized['retry_count'], normalized['tolerance_px'], normalized['settle_ms']), (5, 0, 200))

    def test_reject_non_web_urls(self):
        for url in ('file:///tmp/a', 'javascript:alert(1)', 'https://'):
            with self.assertRaises(ValueError):
                launcher.launch_browser('Firefox', url)

    def test_selected_browser_argument_list(self):
        with patch.object(launcher, 'browser_executable', return_value='/usr/bin/firefox'), patch.object(launcher.subprocess, 'Popen') as popen:
            popen.return_value.wait.return_value = 0
            launcher.launch_browser('Firefox', 'https://example.com/?x=$(id)')
            self.assertEqual(popen.call_args.args[0], ['/usr/bin/firefox', 'https://example.com/?x=$(id)'])


class CallbackTests(unittest.TestCase):
    def make_app(self):
        from unittest.mock import Mock
        instance = app.App.__new__(app.App)
        instance.armed = True
        instance.reliability = dict(app.DEFAULT_RELIABILITY)
        instance.retry_enabled_var = Mock(get=lambda: True)
        instance.retry_count_var = Mock(get=lambda: '3')
        instance.tolerance_var = Mock(get=lambda: '2')
        instance.settle_var = Mock(get=lambda: '500')
        instance.note = Mock()
        instance.log = Mock()
        return instance

    def test_save_callback_applies_persisted_values_and_disarms(self):
        instance = self.make_app()
        with tempfile.TemporaryDirectory() as d, patch.object(app, 'CONFIG', Path(d)/'config.json'):
            self.assertTrue(instance.apply_reliability())
            self.assertFalse(instance.armed)
            self.assertEqual(instance.reliability, app.load_reliability())
            self.assertEqual(instance.reliability['settle_ms'], 500)

    def test_failed_save_keeps_runtime_values_and_shows_error(self):
        instance = self.make_app()
        before = dict(instance.reliability)
        with patch.object(app, 'save_reliability', side_effect=OSError('disk full')):
            self.assertFalse(instance.apply_reliability())
        self.assertEqual(instance.reliability, before)
        self.assertEqual(instance.note.call_args.args[0], 'ERROR')

    def test_launch_button_uses_saved_url_and_selected_browser(self):
        from unittest.mock import Mock
        instance = self.make_app()
        instance.browser = 'Firefox'
        instance.launch_url_var = Mock(get=lambda: ' https://example.com/ ')
        with tempfile.TemporaryDirectory() as d, patch.object(app, 'CONFIG', Path(d)/'config.json'), patch.object(launcher, 'launch_browser') as launch:
            instance.launch_browser()
            launch.assert_called_once_with('Firefox', 'https://example.com/')
            self.assertEqual(app.read_config()['launch_url'], 'https://example.com/')

class PointerPolicyTests(unittest.TestCase):
    def setUp(self):
        guard = patch.object(app, 'verify_window', return_value=True)
        self.guard = guard.start()
        self.addCleanup(guard.stop)

    def make_app(self, tolerance):
        import threading
        import queue
        from unittest.mock import Mock
        instance = app.App.__new__(app.App)
        instance.action_lock = threading.Lock()
        instance.armed = True
        instance.target = (100, 100)
        instance.target_window = {'id': 'saved-browser'}
        instance.browser = 'Firefox'
        instance.reliability = dict(app.DEFAULT_RELIABILITY, tolerance_px=tolerance)
        instance.click_count = 0
        instance.events = queue.Queue()
        instance.log = Mock()
        instance.note = Mock()
        instance.validate_target = Mock(return_value=[{'name':'screen', 'x':0, 'y':0, 'w':1920, 'h':1080}])
        return instance

    def test_configured_tolerance_allows_verified_click(self):
        instance = self.make_app(2)
        positions = [(10,10), (101,100), (101,100), (100,100), (10,10)]
        with patch.object(app, 'pointer_position', side_effect=positions), patch.object(app, 'move_to'), patch.object(app, 'click_at') as click, patch.object(app.time, 'sleep'):
            self.assertTrue(instance.execute_action(True, 'Audio'))
            click.assert_called_once()
            self.assertEqual(instance.click_count, 1)

    def test_exact_tolerance_blocks_missed_position_and_disarms(self):
        instance = self.make_app(0)
        with patch.object(app, 'pointer_position', side_effect=[(10,10), (101,100)]), patch.object(app, 'move_to'), patch.object(app, 'click_at') as click, patch.object(app.time, 'sleep'):
            self.assertFalse(instance.execute_action(True, 'Audio'))
            click.assert_not_called()
            self.assertFalse(instance.armed)

    def test_enabled_retry_can_recover_before_click(self):
        instance = self.make_app(0)
        instance.reliability.update(retries_enabled=True, retry_count=1)
        positions = [(10,10), (101,100), (100,100), (100,100), (100,100), (10,10)]
        with patch.object(app, 'pointer_position', side_effect=positions), patch.object(app, 'move_to') as move, patch.object(app, 'click_at') as click, patch.object(app.time, 'sleep'):
            self.assertTrue(instance.execute_action(True, 'Audio'))
            click.assert_called_once()
            self.assertEqual(move.call_count, 3)  # two attempts, then restore

    def test_covered_window_blocks_click_and_disarms(self):
        instance = self.make_app(2)
        self.guard.side_effect = RuntimeError('Browser covered')
        with patch.object(app, 'pointer_position', side_effect=[(10,10), (100,100)]), patch.object(app, 'move_to'), patch.object(app, 'click_at') as click, patch.object(app.time, 'sleep'):
            self.assertFalse(instance.execute_action(True, 'Audio'))
            click.assert_not_called()
            self.assertFalse(instance.armed)

    def test_window_change_at_final_check_blocks_click(self):
        instance = self.make_app(2)
        self.guard.side_effect = [True, RuntimeError('Browser changed')]
        with patch.object(app, 'pointer_position', side_effect=[(10,10), (100,100), (100,100)]), patch.object(app, 'move_to'), patch.object(app, 'click_at') as click, patch.object(app.time, 'sleep'):
            self.assertFalse(instance.execute_action(True, 'Audio'))
            click.assert_not_called()
            self.assertFalse(instance.armed)

if __name__ == '__main__':
    unittest.main()
