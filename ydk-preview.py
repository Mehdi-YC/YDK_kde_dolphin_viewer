#!/usr/bin/env python3
"""
YDK Side Preview thumbnailer.
Skips small sizes (icon thumbnails) — only renders for the preview panel.
"""

import sys
import urllib.request
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "ydk-preview"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

SECTION_COLORS = {
    "main":  (180, 140, 30),
    "extra": (60,  120, 200),
    "side":  (80,  160, 80),
}
BG_COLOR     = (13,  17,  23)
HEADER_COLOR = (22,  27,  34)


def parse_ydk(path):
    sections = {"main": [], "extra": [], "side": []}
    cur = None
    with open(path, "r", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if   line == "#main":  cur = "main"
            elif line == "#extra": cur = "extra"
            elif line == "!side":  cur = "side"
            elif line.isdigit() and cur:
                sections[cur].append(line)
    return sections

def fetch_image(card_id):
    cached = CACHE_DIR / f"{card_id}.jpg"
    if cached.exists():
        return cached
    url = f"https://images.ygoprodeck.com/images/cards_small/{card_id}.jpg"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ydk-preview/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            cached.write_bytes(r.read())
        return cached
    except Exception:
        return None

def _placeholder(draw, x, y, w, h, color):
    draw.rectangle([x, y, x+w-1, y+h-1], fill=(30, 35, 45), outline=color, width=1)
    cx, cy = x + w//2, y + h//2
    draw.line([cx-8, cy, cx+8, cy], fill=color, width=2)
    draw.line([cx, cy-8, cx, cy+8], fill=color, width=2)

def make_preview(ydk_path, out_path, size):
    from PIL import Image, ImageDraw, ImageFont

    size = int(size)

    sections = parse_ydk(ydk_path)
    plan = [(s, sections[s][:40]) for s in ("main", "extra", "side") if sections[s]]
    if not plan:
        sys.exit(1)

    COLS   = 10
    CARD_W = 72
    CARD_H = int(CARD_W * 1.45)  # ~104
    GAP    = 5
    PAD    = 10
    HDR_H  = 26

    PANEL_W = PAD + COLS * (CARD_W + GAP) - GAP + PAD  # fits 10 cards exactly

    def sec_h(ids):
        rows = -(-len(ids) // COLS)
        return HDR_H + rows * (CARD_H + GAP) + PAD

    total_h = PAD + sum(sec_h(ids) + PAD for _, ids in plan)

    canvas = Image.new("RGB", (PANEL_W, total_h), BG_COLOR)
    draw   = ImageDraw.Draw(canvas)

    try:
        font_b = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 11)
    except Exception:
        font_b = ImageFont.load_default()

    y = PAD
    for sec, ids in plan:
        color = SECTION_COLORS[sec]
        draw.rectangle([PAD, y, PANEL_W-PAD, y+HDR_H-2], fill=HEADER_COLOR)
        draw.rectangle([PAD, y, PAD+4, y+HDR_H-2], fill=color)
        draw.text((PAD+12, y+7), f"{sec.upper()}  ·  {len(ids)} cards", font=font_b, fill=color)
        y += HDR_H

        for i, cid in enumerate(ids):
            col = i % COLS
            row = i // COLS
            x  = PAD + col * (CARD_W + GAP)
            cy = y + row * (CARD_H + GAP)
            img_path = fetch_image(cid)
            if img_path:
                try:
                    card_img = Image.open(img_path).convert("RGB").resize((CARD_W, CARD_H), Image.LANCZOS)
                    canvas.paste(card_img, (x, cy))
                    draw.rectangle([x, cy, x+CARD_W-1, cy+CARD_H-1], outline=(*color, 160), width=1)
                except Exception:
                    _placeholder(draw, x, cy, CARD_W, CARD_H, color)
            else:
                _placeholder(draw, x, cy, CARD_W, CARD_H, color)

        rows = -(-len(ids) // COLS)
        y += rows * (CARD_H + GAP) + PAD

    # Scale to requested width
    scale = size / PANEL_W
    out_h = min(int(total_h * scale), 4096)
    canvas = canvas.resize((size, out_h), Image.LANCZOS)
    canvas.save(out_path, "PNG")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(1)
    try:
        make_preview(sys.argv[1], sys.argv[2], sys.argv[3])
    except Exception:
        sys.exit(1)
