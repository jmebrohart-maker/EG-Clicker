"""Regressions for live monitor coordinates differing from stored KScreen origin."""
import json
import unittest
from unittest.mock import patch
import eg_platform as platform

LIVE = '''--- monitor[0] ---
name HDMI-A-1
x 0
y 0
width 1920
height 1080
scale 1
--- monitor[1] ---
name DP-3
x 1920
y 0
width 1920
height 1080
scale 1
'''

class CoordinateTests(unittest.TestCase):
    def test_user_log_origin_mismatch_uses_live_coordinates(self):
        configured = {'outputs':[
            {'name':'HDMI-A-1','enabled':True,'pos':{'x':2048,'y':0},'size':{'width':1920,'height':1080}},
            {'name':'DP-3','enabled':True,'pos':{'x':3968,'y':0},'size':{'width':1920,'height':1080}}]}
        def command(*args,**kwargs):
            return LIVE if args[0]=='waytool' else json.dumps(configured)
        with patch.object(platform,'run_cmd',side_effect=command) as run:
            screens=platform._linux_screens()
        self.assertEqual([s['x'] for s in screens],[0,1920])
        self.assertEqual(platform.find_screen(1719,494,screens),'HDMI-A-1')
        self.assertEqual(platform.find_screen(3149,748,screens),'DP-3')
        run.assert_called_once_with('waytool','monitors',timeout=8)

    def test_negative_live_coordinates_are_preserved(self):
        screens=platform.parse_waytool_monitors(LIVE.replace('x 0\n','x -1920\n',1).replace('x 1920\n','x 0\n',1))
        self.assertEqual(platform.find_screen(-100,100,screens),'HDMI-A-1')

    def test_invalid_monitor_data_is_rejected(self):
        for value in ('',LIVE.replace('width 1920','width 0'),LIVE.replace('name DP-3','name HDMI-A-1')):
            with self.assertRaises(ValueError):platform.parse_waytool_monitors(value)
