"""Real Tk callback integration tests; run under an X server (or Xvfb)."""
import os
from pathlib import Path
import tempfile
import threading
import time
import tkinter as tk
import unittest
from unittest.mock import patch
from test_app import app

@unittest.skipUnless(os.environ.get('DISPLAY'), 'Requires an X display')
class GuiTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        root=tk.Tk();self.root=root
        original=app.LogWriter
        for patcher in (patch.object(app,'CONFIG',Path(self.temp.name)/'config.json'),
                        patch.object(app,'LogWriter',side_effect=lambda:original(Path(self.temp.name)/'app.log')),
                        patch.object(app.App,'audio_watcher'), patch.object(app.App,'refresh_diagnostics')):
            patcher.start();self.addCleanup(patcher.stop)
        self.error=patch.object(app.messagebox,'showerror');self.dialog=self.error.start();self.addCleanup(self.error.stop)
        self.ui=app.App(root)
        self.ui.target=(100,100);self.ui.saved_layout=[]
        self.ui.target_window={'id':'browser','image':'firefox','class':'firefox'}
        self.ui.audio=False
        self.addCleanup(self.shutdown)

    def shutdown(self):
        self.ui.running=False
        for ident in self.root.tk.call('after','info'):
            self.root.after_cancel(ident)
        self.root.destroy()

    def pump_until(self, condition):
        deadline=time.monotonic()+2
        while time.monotonic()<deadline:
            self.root.update();self.ui.refresh_once()
            if condition():return
            time.sleep(.01)
        self.fail('GUI state did not update before timeout')

    def test_real_arm_and_disarm_button_callbacks(self):
        with patch.object(self.ui,'validate_target',return_value=[]):
            self.ui.arm_button.invoke()
            self.pump_until(lambda:self.ui.armed)
            self.ui.arm_button.invoke();self.ui.refresh_once()
            self.assertFalse(self.ui.armed)
            self.dialog.assert_not_called()

    def test_slow_validation_keeps_cancel_and_logs_responsive(self):
        gate=threading.Event()
        with patch.object(self.ui,'validate_target',side_effect=lambda:gate.wait(2)):
            self.ui.arm_button.invoke()
            self.assertTrue(self.ui.arming)
            self.ui.show_logs();self.root.update()
            self.assertTrue(self.ui.log_window.winfo_exists())
            self.ui.arm_button.invoke()
            self.assertFalse(self.ui.arming)
            gate.set()
        self.assertFalse(self.ui.armed)

    def test_missing_binding_has_visible_error_and_log(self):
        self.ui.target_window=None
        with patch.object(self.ui,'validate_target',return_value=[]):
            self.ui.arm_button.invoke()
            self.pump_until(lambda:not self.ui.arming)
        self.dialog.assert_called_once()
        self.assertIn('browser identity',self.dialog.call_args.args[1])
        self.assertTrue(any('Cannot arm' in line for line in self.ui.history))

    def test_callback_exception_stops_clicks_and_opens_copyable_logs(self):
        self.ui.armed=True
        self.ui.arm_button.configure(command=lambda:1/0)
        self.ui.arm_button.invoke();self.ui.refresh_once();self.root.update()
        self.assertFalse(self.ui.armed)
        self.assertTrue(self.ui.log_window.winfo_exists())
        self.assertIn('ZeroDivisionError',self.ui.log_viewer.get('1.0','end'))
        self.ui.copy_logs()
        self.assertIn('ZeroDivisionError',self.root.clipboard_get())
