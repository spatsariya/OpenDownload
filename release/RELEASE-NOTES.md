# OpenDownload 0.1.0 — Windows preview

The first public preview of an independent, focused download manager for Windows.

## Install

Download **OpenDownload-0.1.0-x64.msi** from the assets below, open it, and follow
the setup wizard. Python is bundled. Setup adds desktop and Start menu shortcuts.
The default location is `%LOCALAPPDATA%\Programs\OpenDownload`.

The app and installer are **unsigned**. Windows may show an unknown-publisher
notice. `SHA256SUMS.txt` is provided to verify the downloaded file's bytes.

## Included

- Direct HTTP/HTTPS downloads with segmented transfers when supported.
- Pause/resume, queue management, saved history, and a total speed limit.
- Search, sorting, status filters, and a compact details pane.

## Validation

- Seven local HTTP transfer tests passed, including byte integrity and resume.
- Frozen executable and installed executable startup checks passed.
- MSI installation, desktop/Start menu shortcuts, and uninstall checked on Windows 11 x64.

## Preview limitations

No browser interception, authenticated browser sessions, video extraction,
scheduled starts, or automatic retries. Resume depends on server range support and
file validators. Testing on other computers remains limited.

Uninstall through Windows Settings → Apps → Installed apps → OpenDownload.
Downloaded files and local history are preserved. History stores URLs locally,
including any private signed links that you add.
