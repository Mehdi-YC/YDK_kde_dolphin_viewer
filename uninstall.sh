#!/usr/bin/env bash
set -e
echo "=== YDK Uninstaller ==="

sudo rm -f /usr/local/bin/ydk-preview
sudo rm -f /usr/local/bin/ydk-open
sudo rm -f /usr/share/thumbnailers/ydk.thumbnailer
sudo rm -f /usr/share/applications/ydk-open.desktop
sudo rm -f /usr/share/mime/packages/ydk.xml
sudo update-mime-database /usr/share/mime
sudo update-desktop-database /usr/share/applications
rm -rf ~/.cache/thumbnails/ ~/.cache/ydk-preview/ 2>/dev/null || true

echo "=== Done! ==="
