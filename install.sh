#!/usr/bin/env bash
# YDK v3 — Installer
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== YDK v3 Installer ==="

echo "▸ Checking Pillow..."
python3 -c "from PIL import Image" 2>/dev/null && echo "  ✓ OK" || {
    pip3 install --user pillow 2>/dev/null || echo "  ⚠ Run: pip3 install --user pillow"
}

echo "▸ Installing scripts..."
sudo install -m 755 "$DIR/ydk-preview.py" /usr/local/bin/ydk-preview
sudo install -m 755 "$DIR/ydk-open.py"    /usr/local/bin/ydk-open
echo "  ✓ Done"

echo "▸ Registering MIME type..."
sudo cp "$DIR/ydk-mime.xml" /usr/share/mime/packages/ydk.xml
sudo update-mime-database /usr/share/mime
echo "  ✓ Done"

echo "▸ Installing thumbnailer..."
sudo cp "$DIR/ydk.thumbnailer" /usr/share/thumbnailers/ydk.thumbnailer
echo "  ✓ Done"

echo "▸ Installing application entry..."
sudo cp "$DIR/ydk-open.desktop" /usr/share/applications/ydk-open.desktop
sudo update-desktop-database /usr/share/applications
xdg-mime default ydk-open.desktop text/x-ydk
echo "  ✓ Done"

echo "▸ Clearing caches..."
rm -rf ~/.cache/thumbnails/ 2>/dev/null || true
echo "  ✓ Done"

echo ""
echo "=== Done! ==="
echo "  • Double-click .ydk → opens in browser (10-per-row, hover side panel)"
echo "  • Preview panel in Dolphin (F11) → card grid preview, no icon thumbnails"
