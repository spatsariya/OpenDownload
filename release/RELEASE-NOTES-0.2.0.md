# OpenDownload 0.2.0 — Cross-platform preview

## Downloads

- **Windows x64:** open the MSI installer.
- **macOS Apple Silicon / Intel:** choose the matching DMG, open it, and drag OpenDownload to Applications. Built and startup-tested on macOS 15. The app is not notarized with Apple; macOS may block opening it.
- **Linux x64 (Ubuntu 22.04+ / compatible Debian systems):** use `sudo apt install ./OpenDownload-0.2.0-Linux-amd64.deb`. Alternatively, extract the tar.gz and run `./OpenDownload/install.sh` for a per-user installation. A graphical desktop is required.
- **Android 10+:** download the signed APK and allow installation from your browser when Android asks. This is a sideloaded preview, not a Google Play release.

## Android is a smaller native app

Android uses the system DownloadManager for background HTTP/HTTPS downloads,
progress, completion notifications, and opening downloaded files. Long-press a
download to cancel/remove it and delete its file. Files save to public Downloads.
There is no manual pause/resume, segmentation, or speed limit in the Android app.
Android manages network waits and background transfers itself.

## Desktop

The desktop apps share the same transfer engine and compact interface, with
server-dependent segmented transfers, pause/resume, queues, and speed limits.
History uses the native application-data location on each OS.

## Validation and limitations

Native builds, transfer tests, and packaged UI startup checks run on each desktop
platform. Android runs lint plus an emulator check that launches the app and
downloads a local test file through the system service, verifying its bytes.
These checks do not replace testing on a wide range of real computers and phones.
Desktop releases are unsigned/not notarized. Android is signed with a persistent
project key, stored outside the source repository. SHA256SUMS.txt covers all assets.

No browser interception, authenticated browser sessions, video extraction, or
torrent support. This is an independent application, not an IDM modification.
