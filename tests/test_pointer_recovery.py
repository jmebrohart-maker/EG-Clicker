"""Transient KWin reads must recover without inventing coordinates or input."""
import unittest
from unittest.mock import patch
import eg_platform as platform
from test_coordinates import LIVE

class PointerReadTests(unittest.TestCase):
    def test_empty_read_recovers_with_live_negative_coordinates(self):
        with patch.object(platform, 'run_cmd', side_effect=['', 'X=-123\nY=456\nSCREEN=0']), patch.object(platform.time, 'sleep'):
            self.assertEqual(platform.pointer_position(), (-123, 456))

    def test_partial_or_empty_reads_never_use_a_previous_position(self):
        with patch.object(platform, 'run_cmd', side_effect=['x:12', '', 'not coordinates']) as run, patch.object(platform.time, 'sleep'), patch.object(platform, 'click_at') as click:
            with self.assertRaisesRegex(RuntimeError, 'after 3 reads'):
                platform.pointer_position()
            self.assertEqual(run.call_count, 3)
            click.assert_not_called()

    def test_read_command_error_can_recover(self):
        with patch.object(platform, 'run_cmd', side_effect=[RuntimeError('DBus busy'), 'x:34 y:56']), patch.object(platform.time, 'sleep'):
            self.assertEqual(platform.pointer_position(), (34, 56))

    def test_coordinate_reads_are_fresh_not_cached(self):
        with patch.object(platform, 'run_cmd', side_effect=['x:1 y:2', '', '', '']), patch.object(platform.time, 'sleep'):
            self.assertEqual(platform.pointer_position(), (1, 2))
            with self.assertRaises(RuntimeError):
                platform.pointer_position()

    def test_monitor_health_rejects_empty_success(self):
        with patch.object(platform, 'run_cmd', return_value=''):
            with self.assertRaisesRegex(RuntimeError, 'Reconnect pointer'):
                platform.pointer_health()

    def test_reconnect_starts_service_then_checks_both_backends(self):
        with patch.object(platform, 'run_cmd') as run, patch.object(platform, 'pointer_health', side_effect=[RuntimeError('waiting for consent'), LIVE]), patch.object(platform, 'pointer_position', return_value=(12, 34)) as position, patch.object(platform.time, 'sleep'), patch.object(platform, 'move_to') as move, patch.object(platform, 'click_at') as click:
            self.assertEqual(platform.connect_pointer(), LIVE)
            run.assert_called_once_with('systemctl', '--user', 'start', '--no-block', 'waytool.service', timeout=5, trace=None)
            position.assert_called_once_with(None)
            move.assert_not_called(); click.assert_not_called()

    def test_reconnect_has_a_deadline_without_repeated_service_starts(self):
        with patch.object(platform, 'run_cmd') as run, patch.object(platform, 'pointer_health', side_effect=RuntimeError('no consent')), patch.object(platform.time, 'monotonic', side_effect=[0, 0, 46]), patch.object(platform.time, 'sleep'):
            with self.assertRaisesRegex(RuntimeError, 'desktop-control prompt'):
                platform.connect_pointer()
            self.assertEqual(run.call_count, 1)
