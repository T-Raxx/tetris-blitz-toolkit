import json, base64, pathlib, html

def _b64(path):
    return "data:image/png;base64," + base64.b64encode(pathlib.Path(path).read_bytes()).decode()

def render_html(cache_dir="discovery_cache", out_html=None):
    cache = pathlib.Path(cache_dir)
    catalog = json.loads((cache / "catalog.json").read_text(encoding="utf-8"))
    out_html = out_html or str(cache / "discovery.html")
    cats = sorted(catalog.get("counts", {}))
    chips = "".join(f'<label><input type=checkbox class=cf value="{c}" checked> {c} '
                    f'({catalog["counts"][c]})</label>' for c in cats)
    cards = []
    for f in catalog["findings"]:
        thumbs = f.get("thumbs") or []
        img = (f'<img src="{_b64(thumbs[0])}">' if thumbs and pathlib.Path(thumbs[0]).exists()
               else '<div class="noimg">no sprite</div>')
        txt = html.escape((f["title"] + " " + f["status"] + " " + f["source_file"]).lower())
        cards.append(
            f'<div class="card" data-cat="{f["category"]}" data-txt="{txt}">{img}'
            f'<div class="t">{html.escape(f["title"])}</div>'
            f'<div class="s">{html.escape(f["status"])}</div>'
            f'<div class="src">{html.escape(f["source_file"])}</div></div>')
    total = sum(catalog.get("counts", {}).values())
    doc = f"""<!doctype html><meta charset=utf-8><title>Tetris Blitz — Hidden Content</title>
<style>
body{{background:#15161c;color:#e6e6e6;font:13px system-ui;margin:0;padding:16px}}
h1{{font-size:18px}} .bar{{position:sticky;top:0;background:#15161c;padding:8px 0}}
.bar input[type=text]{{width:260px;padding:6px;background:#23252f;border:1px solid #333;color:#eee;border-radius:6px}}
label{{margin-right:10px;white-space:nowrap}}
.grid{{display:flex;flex-wrap:wrap;gap:10px;margin-top:10px}}
.card{{background:#20222b;border:1px solid #2c2e38;border-radius:8px;padding:8px;width:150px}}
.card img{{width:64px;height:64px;object-fit:contain;image-rendering:pixelated;display:block;margin:0 auto 6px}}
.noimg{{width:64px;height:64px;display:flex;align-items:center;justify-content:center;color:#666;margin:0 auto 6px;border:1px dashed #333}}
.t{{font-weight:600;word-break:break-word}} .s{{color:#8fd18f;font-size:11px}} .src{{color:#888;font-size:10px}}
</style>
<h1>Tetris Blitz — Hidden Content ({total} findings)</h1>
<div class="bar"><input type=text id=q placeholder="search…"> {chips}</div>
<div class="grid" id=g>{"".join(cards)}</div>
<script>
const q=document.getElementById('q'), cbs=[...document.querySelectorAll('.cf')];
function apply(){{
  const s=q.value.toLowerCase(), on=new Set(cbs.filter(c=>c.checked).map(c=>c.value));
  for(const el of document.querySelectorAll('.card')){{
    el.style.display=(on.has(el.dataset.cat)&&el.dataset.txt.includes(s))?'':'none';
  }}
}}
q.oninput=apply; cbs.forEach(c=>c.onchange=apply);
</script>"""
    pathlib.Path(out_html).write_text(doc, encoding="utf-8")
    return out_html
