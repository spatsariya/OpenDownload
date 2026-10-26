"""Prepare text assets for the first public release without publishing anything."""
from pathlib import Path
import hashlib

root = Path(__file__).resolve().parents[1]
installer = root / 'release' / 'OpenDownload-0.1.0-x64.msi'
(root/'release'/'SHA256SUMS.txt').write_text(
    hashlib.sha256(installer.read_bytes()).hexdigest()+'  '+installer.name+'\n', encoding='ascii')
(root/'README.md').write_text(r'''# OpenDownload

A compact, independent download manager for Windows. No account or subscription.

**[Download Windows installer](https://github.com/spatsariya/OpenDownload/releases/download/v0.1.0/OpenDownload-0.1.0-x64.msi)** · **[Project website](https://spatsariya.github.io/OpenDownload/)** · **[Release notes](https://github.com/spatsariya/OpenDownload/releases/tag/v0.1.0)**

![OpenDownload interface with illustrative sample downloads](docs/assets/app-preview.png)

## Install

1. Download **OpenDownload-0.1.0-x64.msi** from [Releases](https://github.com/spatsariya/OpenDownload/releases).
2. Open it and follow the setup wizard. Python is included.
3. Launch OpenDownload from your desktop or Start menu, choose **Add download**, and paste a direct HTTP or HTTPS file link.

This is an **unsigned preview release**. Windows may show an unknown-publisher
notice. Compare your download against `SHA256SUMS.txt` on the release to verify its
bytes. Tested on Windows 11 x64; testing on other computers is still limited.

Default installation: `%LOCALAPPDATA%\Programs\OpenDownload`.
Uninstall through Windows Settings → Apps → Installed apps → OpenDownload.
Uninstall preserves your downloaded files, partial downloads, and history.

## Features

- Single or segmented HTTP/HTTPS downloads with 1, 2, 4, or 8 connections.
- Server-dependent pause/resume and local saved history.
- Two simultaneous downloads, queue controls, and a total speed limit.
- Compact interface with search, sorting, status filters, and a details pane.
- Existing destination files are never overwritten.

Resume and segmentation require server support and stable file validators. If a
remote file changes, partial data is discarded and the transfer starts again.
Filenames come from the URL rather than Content-Disposition.

## Preview limitations

Browser interception, authenticated browser sessions, video extraction, scheduled
start times, automatic retries, tray integration, and torrent support are not
included. Failed downloads can be retried manually with Resume. This app does not
claim feature parity with other download managers.

History is saved locally in `%LOCALAPPDATA%\OpenDownload\history.json`, including
URLs and any private signed links you add. Partial files live beside the chosen
destination in `.opendownload-<id>` folders. Removing a row removes history only;
it preserves downloaded and partial files.

## Run from source

Requires Python with Tkinter; the app itself uses only the Python standard library.

```powershell
python app.py
```

## Tests

```powershell
python -m unittest -v test_engine.py
```

Seven local HTTP tests check segmented byte integrity, pause/resume, completion
edge cases, non-range fallback, overwrite protection, history, and URL validation.
The packaged and installed app also passed Tk startup checks. MSI installation,
shortcuts, and uninstall were checked on Windows 11 x64.

## Build the Windows installer

Requires Windows x64, Python 3.14, .NET SDK, and network access for build tools.

```powershell
powershell -File packaging\build.ps1
```

The build uses pinned PyInstaller and WiX Toolset versions. The installer appears
in `release/OpenDownload-0.1.0-x64.msi`. The MSI is intentionally not committed to
Git; distribution binaries live in GitHub Releases.

## Website

The static GitHub Pages site is in `docs/`. Preview locally:

```powershell
python -m http.server 8765 --directory docs --bind 127.0.0.1
```

Interface screenshots use clearly labeled sample downloads, not user history.

## Feedback

[Report a bug](https://github.com/spatsariya/OpenDownload/issues) with your Windows
version, app version, expected behavior, and any error message. Remove private
URLs, tokens, and personal file paths before sharing diagnostics.
''', encoding='utf-8')
print('README and release checksum prepared')
