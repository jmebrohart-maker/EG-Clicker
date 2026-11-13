import ctypes as C
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import eg_platform as platform
import window_guard as guard

class InputAbiTests(unittest.TestCase):
    def test_sdk_sizes(self):
        self.assertEqual(C.sizeof(platform.POINT),8)
        self.assertEqual(C.sizeof(platform.RECT),16)
        self.assertEqual(C.sizeof(platform.INPUT),40 if C.sizeof(C.c_void_p)==8 else 28)

    def test_click_is_single_down_up_pair(self):
        api=Mock();api.SendInput.return_value=2
        with patch.object(platform,'_user32',return_value=api):platform.click_at((100,100))
        args=api.SendInput.call_args.args
        self.assertEqual(args[0],2)
        self.assertEqual([args[1][i].mi.dwFlags for i in (0,1)],[2,4])

    def test_partial_input_releases_button_and_does_not_retry_click(self):
        api=Mock();api.SendInput.side_effect=[1,1]
        with patch.object(platform,'_user32',return_value=api),self.assertRaises(RuntimeError):platform.click_at((100,100))
        self.assertEqual(api.SendInput.call_count,2)
        self.assertEqual(api.SendInput.call_args.args[0],1)
        self.assertEqual(api.SendInput.call_args.args[1].contents.mi.dwFlags,4)

    def test_elevated_app_input_block_fails_closed(self):
        api=Mock();api.SendInput.return_value=0
        with patch.object(platform,'_user32',return_value=api),self.assertRaisesRegex(RuntimeError,'blocked input'):platform.click_at((100,100))
        self.assertEqual(api.SendInput.call_count,1)

    @unittest.skipUnless(os.name=='nt','Native Win32 read-only check')
    def test_read_only_native_api(self):
        point=platform.pointer_position()
        self.assertEqual(len(point),2)
        self.assertTrue(platform.screen_layout())

class AudioIsolationTests(unittest.TestCase):
    def session(self,name,peak=0,state=1,fail=False):
        meter=Mock();meter.GetPeakValue.return_value=peak
        control=Mock()
        if fail:control.QueryInterface.side_effect=RuntimeError('meter failed')
        else:control.QueryInterface.return_value=meter
        return SimpleNamespace(Process=SimpleNamespace(name=lambda:name),State=state,_ctl=control)

    def test_other_apps_do_not_count_as_browser_audio(self):
        sessions=[self.session('firefox.exe',0),self.session('music.exe',1)]
        with patch.object(platform,'_audio_backend',return_value=(sessions,object())):
            self.assertEqual(platform.browser_audio_state('Firefox'),(False,None))

    def test_selected_browser_peak_detected(self):
        with patch.object(platform,'_audio_backend',return_value=([self.session('msedge.exe',0.1)],object())):
            self.assertEqual(platform.browser_audio_state('Edge'),(True,None))
            self.assertEqual(platform.browser_audio_state('Firefox'),(False,None))

    def test_chromium_selection_does_not_match_a_chrome_process(self):
        with patch.object(platform,'_audio_backend',return_value=([self.session('chrome.exe',0.2)],object())):
            self.assertEqual(platform.browser_audio_state('Chromium'),(False,None))

    def test_meter_failure_never_becomes_silence(self):
        with patch.object(platform,'_audio_backend',return_value=([self.session('firefox.exe',fail=True)],object())):
            state,error=platform.browser_audio_state('Firefox')
        self.assertIsNone(state);self.assertIn('unavailable',error)

class WindowsWindowTests(unittest.TestCase):
    def setUp(self):
        self.record=dict(id='123',active='123',pid=100,image='firefox.exe',started='10000',geometry=[0,0,1920,1080],pointer=[100,100],**{'class':'mozillawindowclass'})
        patcher=patch.object(guard,'window_snapshot',side_effect=lambda:dict(self.record));patcher.start();self.addCleanup(patcher.stop)
        self.saved=guard.capture_window('Firefox',(100,100))

    def test_captured_browser_verifies(self):self.assertTrue(guard.verify_window(self.saved,'Firefox',(100,100),0))
    def test_inactive_browser_rejected(self):
        self.record['active']='456'
        with self.assertRaises(RuntimeError):guard.verify_window(self.saved,'Firefox',(100,100),0)
    def test_restarted_process_rejected(self):
        self.record['started']='20000'
        with self.assertRaises(RuntimeError):guard.verify_window(self.saved,'Firefox',(100,100),0)
    def test_foreign_process_rejected(self):
        self.record['image']='other.exe'
        with self.assertRaises(RuntimeError):guard.capture_window('Firefox',(100,100))
    def test_resized_window_rejected(self):
        self.record['geometry']=[0,0,1000,1000]
        with self.assertRaises(RuntimeError):guard.verify_window(self.saved,'Firefox',(100,100),0)
