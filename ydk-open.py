#!/usr/bin/env python3
"""
YDK HTML Viewer — opens deck as interactive HTML in the browser.
Usage: ydk-open <deck.ydk>
"""

import sys
import os
import json
import tempfile
import subprocess
from pathlib import Path

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

def generate_html(sections, deck_name):
    # Build sections data for JS
    js_sections = []
    for sec in ("main", "extra", "side"):
        ids = sections[sec]
        if ids:
            js_sections.append({"name": sec, "ids": ids})

    sections_json = json.dumps(js_sections)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{deck_name}</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --bg:      #111;
    --surface: #1a1a1a;
    --border:  #2a2a2a;
    --gold:    #c8960c;
    --blue:    #3a6db5;
    --green:   #3a8a3a;
    --text:    #ddd;
    --sub:     #666;
    --card-w:  88px;
    --card-h:  128px;
    --panel:   260px;
  }}

  html, body {{ height: 100%; background: var(--bg); color: var(--text); font: 13px/1.5 monospace; }}

  #app {{ display: flex; height: 100vh; overflow: hidden; }}

  /* ── left panel ── */
  #side {{
    width: var(--panel);
    min-width: var(--panel);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: var(--surface);
  }}

  #side-hint {{
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--sub);
    font-size: 11px;
    padding: 20px;
    text-align: center;
  }}

  #card-detail {{ display: none; flex-direction: column; height: 100%; overflow: hidden; }}
  #card-detail.visible {{ display: flex; }}

  #card-img-wrap {{
    padding: 14px;
    flex-shrink: 0;
    border-bottom: 1px solid var(--border);
  }}

  #card-img-wrap img {{
    width: 100%;
    aspect-ratio: 59/86;
    object-fit: cover;
    display: block;
    background: #222;
  }}

  #card-info {{
    padding: 12px;
    overflow-y: auto;
    flex: 1;
    scrollbar-width: thin;
    scrollbar-color: var(--border) transparent;
  }}

  #card-name {{
    font-size: 12px;
    font-weight: bold;
    color: var(--text);
    line-height: 1.4;
    margin-bottom: 6px;
  }}

  #card-type {{ font-size: 10px; color: var(--sub); margin-bottom: 8px; }}

  #card-stats {{
    font-size: 11px;
    color: var(--text);
    margin-bottom: 10px;
    padding: 6px 8px;
    background: var(--bg);
    border-left: 2px solid var(--border);
  }}

  #card-desc {{
    font-size: 10px;
    line-height: 1.6;
    color: #aaa;
    border-top: 1px solid var(--border);
    padding-top: 8px;
    margin-top: 2px;
  }}

  /* ── main grid area ── */
  #main {{
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    scrollbar-width: thin;
    scrollbar-color: var(--border) transparent;
  }}

  #deck-title {{
    font-size: 11px;
    color: var(--sub);
    letter-spacing: .15em;
    text-transform: uppercase;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
  }}

  .section {{ margin-bottom: 20px; }}

  .section-header {{
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    font-size: 10px;
    letter-spacing: .12em;
    color: var(--sub);
    text-transform: uppercase;
  }}

  .section-pip {{ width: 6px; height: 6px; flex-shrink: 0; }}

  .section-count {{ margin-left: auto; }}

  .card-grid {{
    display: grid;
    grid-template-columns: repeat(10, var(--card-w));
    gap: 4px;
  }}

  .card-slot {{
    width: var(--card-w);
    height: var(--card-h);
    cursor: pointer;
    overflow: hidden;
    border: 1px solid var(--border);
    transition: border-color .1s, opacity .1s;
    position: relative;
  }}

  .card-slot:hover, .card-slot.active {{
    border-color: var(--text);
    z-index: 5;
  }}

  .card-slot.active {{ border-color: var(--gold); }}

  .card-slot img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    background: #1a1a1a;
  }}

  .placeholder {{
    width: 100%; height: 100%;
    background: #1a1a1a;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--border);
    font-size: 18px;
  }}
</style>
</head>
<body>
<div id="app">

  <div id="side">
    <div id="side-hint">hover a card</div>
    <div id="card-detail">
      <div id="card-img-wrap"><img id="big-img" src="" alt=""></div>
      <div id="card-info">
        <div id="card-name"></div>
        <div id="card-type"></div>
        <div id="card-stats"></div>
        <div id="card-desc"></div>
      </div>
    </div>
  </div>

  <div id="main">
    <div id="deck-title">{deck_name}</div>
    <div id="sections"></div>
  </div>

</div>
<script>
const SECTIONS = {sections_json};
const SEC_COLORS = {{ main:'#c8960c', extra:'#3a6db5', side:'#3a8a3a' }};
const cache = {{}};
let active = null;

const container = document.getElementById('sections');

SECTIONS.forEach(sec => {{
  const wrap = document.createElement('div');
  wrap.className = 'section';

  const hdr = document.createElement('div');
  hdr.className = 'section-header';
  hdr.innerHTML = `
    <div class="section-pip" style="background:${{SEC_COLORS[sec.name]}}"></div>
    <span style="color:${{SEC_COLORS[sec.name]}}">${{sec.name}}</span>
    <span class="section-count">${{sec.ids.length}}</span>
  `;
  wrap.appendChild(hdr);

  const grid = document.createElement('div');
  grid.className = 'card-grid';

  sec.ids.forEach(id => {{
    const slot = document.createElement('div');
    slot.className = 'card-slot';
    slot.dataset.id = id;

    const img = document.createElement('img');
    img.loading = 'lazy';
    img.src = `https://images.ygoprodeck.com/images/cards_small/${{id}}.jpg`;
    img.onerror = () => img.replaceWith(
      Object.assign(document.createElement('div'), {{ className:'placeholder', textContent:'?' }})
    );
    slot.appendChild(img);
    slot.addEventListener('mouseenter', () => hover(slot));
    grid.appendChild(slot);
  }});

  wrap.appendChild(grid);
  container.appendChild(wrap);
}});

function hover(slot) {{
  if (active) active.classList.remove('active');
  active = slot;
  slot.classList.add('active');
  load(slot.dataset.id);
}}

function load(id) {{
  document.getElementById('side-hint').style.display = 'none';
  document.getElementById('card-detail').classList.add('visible');
  document.getElementById('big-img').src = `https://images.ygoprodeck.com/images/cards/${{id}}.jpg`;

  if (cache[id]) {{ render(cache[id]); return; }}

  document.getElementById('card-name').textContent = '...';
  document.getElementById('card-type').textContent = '';
  document.getElementById('card-stats').textContent = '';
  document.getElementById('card-desc').textContent = '';

  fetch(`https://db.ygoprodeck.com/api/v7/cardinfo.php?id=${{id}}`)
    .then(r => r.json())
    .then(d => {{ cache[id] = d.data[0]; render(d.data[0]); }})
    .catch(() => {{ document.getElementById('card-name').textContent = id; }});
}}

function render(info) {{
  document.getElementById('card-name').textContent = info.name || '';
  document.getElementById('card-type').textContent =
    [info.attribute, info.race, info.type].filter(Boolean).join(' / ');
  document.getElementById('card-stats').textContent =
    info.atk !== undefined ? `ATK ${{info.atk}}  DEF ${{info.def}}` : '';
  document.getElementById('card-desc').textContent = info.desc || '';
}}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ydk-open <deck.ydk>")
        sys.exit(1)

    ydk_path = sys.argv[1]
    if not os.path.isfile(ydk_path):
        print(f"File not found: {ydk_path}")
        sys.exit(1)

    deck_name = Path(ydk_path).stem
    sections  = parse_ydk(ydk_path)
    html      = generate_html(sections, deck_name)

    tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False,
                                     prefix=f"ydk_{deck_name}_",
                                     dir=tempfile.gettempdir(),
                                     mode="w", encoding="utf-8")
    tmp.write(html)
    tmp.close()

    # Open in default browser
    subprocess.Popen(["xdg-open", tmp.name])
