#!/bin/sh
set -eu
# Per-user installation; no root access or system service.
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
target="$HOME/.local/opt/OpenDownload"
mkdir -p "$target" "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/256x256/apps"
if [ "$source_dir" != "$target" ]; then cp -R "$source_dir/." "$target/"; fi
chmod +x "$target/OpenDownload"
cp "$target/icon.png" "$HOME/.local/share/icons/hicolor/256x256/apps/opendownload.png"
# Desktop field codes must be escaped in user-controlled paths.
escaped_target=$(printf '%s' "$target" | sed 's/\\/\\\\/g;s/"/\\"/g;s/`/\\`/g;s/\$/\\$/g;s/%/%%/g')
cat > "$HOME/.local/share/applications/opendownload.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=OpenDownload
Comment=Download manager
Exec="$escaped_target/OpenDownload"
Icon=opendownload
Terminal=false
Categories=Network;FileTransfer;
EOF
printf 'Installed to %s\nLaunch OpenDownload from your applications menu.\n' "$target"
