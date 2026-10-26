import os
import unittest
from pathlib import Path
from unittest.mock import patch
import platform_support as platform


class PlatformTests(unittest.TestCase):
    def setUp(self):
        home=patch('platform_support.Path.home',return_value=Path('/home/test'))
        home.start()
        self.addCleanup(home.stop)

    def test_explicit_data_directory(self):
        with patch.dict(os.environ, {'OPENDOWNLOAD_DATA_DIR': '/test/history'}):
            self.assertEqual(platform.data_directory(),Path('/test/history'))

    def test_native_history_directories(self):
        with patch.dict(os.environ, {}, clear=True), patch('platform_support.sys.platform','darwin'):
            self.assertEqual(platform.data_directory(),Path.home()/'Library'/'Application Support'/'OpenDownload')
        with patch.dict(os.environ, {'XDG_DATA_HOME':'/custom/data'}, clear=True),patch('platform_support.sys.platform','linux'):
            self.assertEqual(platform.data_directory(),Path('/custom/data/OpenDownload'))
        with patch.dict(os.environ, {'LOCALAPPDATA':'C:/local'}, clear=True),patch('platform_support.sys.platform','win32'):
            self.assertEqual(platform.data_directory(),Path('C:/local/OpenDownload'))

    def test_folder_launch_uses_argument_list(self):
        for system,program in [('darwin','open'),('linux','xdg-open')]:
            with patch('platform_support.sys.platform',system),patch('platform_support.subprocess.Popen') as launch:
                platform.open_directory(Path('/some folder'))
                launch.assert_called_once_with([program,str(Path('/some folder'))])


if __name__=='__main__':unittest.main()
