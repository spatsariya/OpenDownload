"""Native Linux/macOS build. Run on the target OS, not a cross-compiler."""
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from platform_support import VERSION
os.chdir(root)
release=root/'release'
release.mkdir(exist_ok=True)
mac=sys.platform=='darwin'
arch=platform.machine()
subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir',
    '--windowed','--name','OpenDownload','--exclude-module','PIL','--exclude-module','pytest',
    *(['--osx-bundle-identifier','io.github.spatsariya.opendownload','--target-arch',arch] if mac else []),
    'app.py'],check=True)
exe=root/'dist'/'OpenDownload.app'/'Contents'/'MacOS'/'OpenDownload' if mac else root/'dist'/'OpenDownload'/'OpenDownload'
report=root/'build'/'native-smoke.json'
subprocess.run([str(exe),'--smoke-test',str(report)],check=True,timeout=90)
assert json.loads(report.read_text())['ok']
if mac:
    staging=root/'build'/'dmg'
    staging.mkdir(exist_ok=True)
    shutil.copytree(root/'dist'/'OpenDownload.app',staging/'OpenDownload.app',dirs_exist_ok=True)
    link=staging/'Applications'
    if not link.exists(): link.symlink_to('/Applications')
    subprocess.run(['hdiutil','create','-volname','OpenDownload','-srcfolder',str(staging),'-ov','-format','UDZO',
        str(release/f'OpenDownload-{VERSION}-macOS-{arch}.dmg')],check=True)
else:
    payload=root/'dist'/'OpenDownload'
    shutil.copy(root/'packaging'/'install-linux.sh',payload/'install.sh')
    (payload/'install.sh').chmod(0o755)
    shutil.copy(root/'docs'/'assets'/'icon.png',payload/'icon.png')
    shutil.copy(root/'README.md',payload/'README.md')
    with tarfile.open(release/f'OpenDownload-{VERSION}-Linux-x86_64.tar.gz','w:gz') as archive:
        archive.add(payload,arcname='OpenDownload')
    deb=root/'build'/'deb'
    shutil.copytree(payload,deb/'opt'/'opendownload',dirs_exist_ok=True)
    control=deb/'DEBIAN';control.mkdir(parents=True,exist_ok=True)
    (control/'control').write_text(f'Package: opendownload\nVersion: {VERSION}\nSection: net\nPriority: optional\nArchitecture: amd64\nMaintainer: OpenDownload\nDepends: libc6 (>= 2.35), libx11-6, libxext6, libxrender1, libxft2, libxss1, libfontconfig1, libfreetype6\nDescription: A compact desktop download manager\n')
    applications=deb/'usr'/'share'/'applications';applications.mkdir(parents=True,exist_ok=True)
    (applications/'opendownload.desktop').write_text('[Desktop Entry]\nType=Application\nName=OpenDownload\nExec=/opt/opendownload/OpenDownload\nIcon=/opt/opendownload/icon.png\nTerminal=false\nCategories=Network;FileTransfer;\n')
    subprocess.run(['dpkg-deb','--build','--root-owner-group',str(deb),str(release/f'OpenDownload-{VERSION}-Linux-amd64.deb')],check=True)
