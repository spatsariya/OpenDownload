"""Desktop integration without shell commands or Windows-only assumptions."""
import os
import sys
import subprocess
from pathlib import Path

VERSION = '0.2.0'


def data_directory():
    if os.environ.get('OPENDOWNLOAD_DATA_DIR'):
        return Path(os.environ['OPENDOWNLOAD_DATA_DIR'])
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'OpenDownload'
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / 'OpenDownload'
    return Path(os.environ.get('XDG_DATA_HOME', str(Path.home()/'.local'/'share')))/'OpenDownload'


def open_directory(path):
    if sys.platform == 'win32':
        os.startfile(str(path))
    else:
        subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', str(path)])
