# Changelog

## 0.2.0 — Cross-platform preview

- Native macOS Apple Silicon and Intel app bundles in DMG images.
- Linux x64 Debian package and portable archive with a per-user installer.
- Native Android 10+ app using the system background download service.
- Native desktop history locations and folder-opening commands.
- Target-OS desktop tests and packaged startup checks; Android lint and emulator download-integrity test.

Android has a smaller feature set: no manual pause/resume, segmentation, or speed
limits. Mac apps are not notarized. Coverage on real devices remains limited.

## 0.1.0 — First public preview

- Compact Windows interface with search, sorting, status filters, and a details pane.
- Direct HTTP and HTTPS downloads, with 1, 2, 4, or 8 connections per file.
- Server-dependent pause/resume, saved history, two simultaneous files, and a total speed limit.
- Windows x64 MSI with bundled Python/Tk, desktop and Start menu shortcuts, and uninstall support.

The installer and app are unsigned. Browser interception, authenticated browser
sessions, video extraction, scheduled starts, and automatic retries are not included.
Resume and segmentation depend on server support. This preview has been tested on
Windows 11 x64; testing on other computers is limited.
