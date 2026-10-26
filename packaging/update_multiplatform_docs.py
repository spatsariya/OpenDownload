"""Update public download links after the cross-platform release passes checks."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
page=root/'docs'/'index.html'
text=page.read_text(encoding='utf-8')
text=text.replace('v0.1.0','v0.2.0').replace('OpenDownload-0.1.0','OpenDownload-0.2.0')
text=text.replace('FOR WINDOWS · v0.2.0 PREVIEW','DESKTOP &amp; ANDROID · v0.2.0 PREVIEW')
text=text.replace('<a href="#features">Features</a>','<a href="downloads.html">All platforms</a>')
text=text.replace('<a class="text-link" href="https://github.com/spatsariya/OpenDownload/releases/tag/v0.2.0">Release notes', '<a class="text-link" href="downloads.html">Mac, Linux &amp; Android')
text=text.replace('THE ESSENTIALS, DONE SIMPLY','DESKTOP ESSENTIALS, DONE SIMPLY')
text=text.replace('An independent download manager for Windows.','An independent download manager for desktop and Android.')
page.write_text(text,encoding='utf-8')
readme=root/'README.md'
text=readme.read_text(encoding='utf-8').replace('v0.1.0','v0.2.0').replace('OpenDownload-0.1.0','OpenDownload-0.2.0')
text=text.replace('A compact, independent download manager for Windows.', 'An independent download manager for Windows, macOS, Linux, and Android.')
text=text.replace('## Install\n','## Install on Windows\n',1)
text=text.replace('## Features\n', '''## macOS, Linux, and Android

Use the [platform download page](https://spatsariya.github.io/OpenDownload/downloads.html).
macOS has separate Apple Silicon and Intel DMGs (not notarized); Linux x64 has
an Ubuntu/Debian .deb and portable archive. Android 10+ has a signed sideloadable APK.

The smaller native Android app uses the system download service for background
HTTP/HTTPS transfers, progress, notifications, and opening completed files. It
does not include manual pause/resume, segmentation, or speed limits. Long-pressing
a row removes the download and deletes its file. This is not a Google Play release.

Desktop builds run engine tests and packaged startup checks on their target OS.
Android runs lint and an emulator download-integrity check. Real-device coverage
remains limited. See the release notes for installation and platform requirements.

## Desktop features
''',1)
readme.write_text(text,encoding='utf-8')
