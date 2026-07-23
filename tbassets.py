import re, pathlib, plistlib
from PIL import Image

ASSETS = pathlib.Path("..") / "Tetris blitz" / "assets" / "Assets"
COCOS = ASSETS / "Cocos2dxImages" / "size150" / "Common"
PLIST = COCOS / "Common0.plist"
ATLAS = COCOS / "Common0.png"

def _color_syms():
    import tbmosaic
    return tbmosaic.symbols("colors")

def color_swatch_map():
    """char -> (r,g,b) swatch, from mosaic_symbols.json (data-driven)."""
    return {ch: tuple(m["swatch"]) for ch, m in _color_syms().items() if m.get("swatch")}

def color_frame_map():
    """char -> Common-atlas frame name, for the chars that have a confident real texture."""
    return {ch: m["frame"] for ch, m in _color_syms().items() if m.get("frame")}

# Back-compat aliases (were hardcoded; now derived from the RE'd symbol table).
def _letter_color():
    return color_swatch_map()
LETTER_COLOR = _letter_color()
BLOCK_FRAMES = sorted(set(color_frame_map().values()))

POWERUP_NAME = {"4": "Bombs", "5": "MeteorStorm", "6": "Magnet", "7": "Blockade",
                "8": "Inversion", "9": "InstantReplay", "A": "MinoRain",
                "B": "LuckySeven", "C": "ThreeStrikes"}
POWERUP_FRAMES = {"4": "Common/helper_bomb.png", "5": "Common/helper_meteor.png",
    "6": "Common/helper_magnet.png", "7": "Common/helper_blockade.png",
    "8": "Common/finisher_inversion.png", "9": "Common/finisher_rewind.png",
    "A": "Common/finisher_minoRain.png", "B": "Common/helper_lucky7.png",
    "C": "Common/helper_trippleI.png"}

def _nums(s):
    return [int(x) for x in re.findall(r"-?\d+", s)]

def extract_atlas(cache_dir, plist=PLIST, atlas=ATLAS, limit=None):
    cache = pathlib.Path(cache_dir); cache.mkdir(parents=True, exist_ok=True)
    pl = plistlib.loads(pathlib.Path(plist).read_bytes())
    frames = pl["frames"]
    img = Image.open(atlas).convert("RGBA")
    out = {}
    for i, (name, meta) in enumerate(frames.items()):
        if limit and i >= limit:
            break
        rect = meta.get("frame") or meta.get("textureRect")
        x, y, w, h = _nums(rect)[:4]
        rotated = bool(meta.get("rotated") or meta.get("textureRotated"))
        if rotated:
            sub = img.crop((x, y, x + h, y + w)).rotate(-90, expand=True)
        else:
            sub = img.crop((x, y, x + w, y + h))
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
        p = cache / (safe if safe.endswith(".png") else safe + ".png")
        sub.save(p); out[name] = str(p)
    return out

def carve_pngs(db_path, out_dir):
    data = pathlib.Path(db_path).read_bytes()
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    sig = b"\x89PNG\r\n\x1a\n"; end = b"IEND"
    paths, i, n = [], data.find(sig), 0
    while i >= 0:
        e = data.find(end, i)
        if e < 0:
            break
        chunk = data[i:e + 8]           # IEND + 4-byte CRC
        p = out / f"carved_{n}.png"; p.write_bytes(chunk)
        paths.append(str(p)); n += 1
        i = data.find(sig, e)
    return paths

def dominant_color(png_path):
    im = Image.open(png_path).convert("RGBA").resize((16, 16))
    data = im.tobytes()                       # RGBA bytes, avoids deprecated getdata()
    rs = gs = bs = k = 0
    for i in range(0, len(data), 4):
        if data[i + 3] > 32:
            rs += data[i]; gs += data[i + 1]; bs += data[i + 2]; k += 1
    k = k or 1
    return (rs // k, gs // k, bs // k)

def auto_map_blocks(sprite_paths, letters):
    doms = [(p, dominant_color(p)) for p in sprite_paths]
    result = {}
    for ch in letters:
        target = LETTER_COLOR.get(ch, (128, 128, 128))
        best = min(doms, key=lambda pd: sum((a - b) ** 2 for a, b in zip(pd[1], target)))
        result[ch] = best[0]
    return result

def extract_named(cache_dir, names, plist=PLIST, atlas=ATLAS):
    """Extract only the given frame keys (skips any missing). Returns key->path."""
    cache = pathlib.Path(cache_dir); cache.mkdir(parents=True, exist_ok=True)
    pl = plistlib.loads(pathlib.Path(plist).read_bytes())
    frames = pl["frames"]; img = Image.open(atlas).convert("RGBA"); out = {}
    for name in names:
        meta = frames.get(name)
        if not meta:
            continue
        x, y, w, h = _nums(meta.get("frame") or meta.get("textureRect"))[:4]
        rotated = bool(meta.get("rotated") or meta.get("textureRotated"))
        sub = (img.crop((x, y, x + h, y + w)).rotate(-90, expand=True) if rotated
               else img.crop((x, y, x + w, y + h)))
        p = cache / (re.sub(r"[^A-Za-z0-9_.-]", "_", name))
        sub.save(p); out[name] = str(p)
    return out

def block_sprite_map(cache_dir, letters=None):
    """char -> extracted PNG path for every color char that has a confident real frame
    in mosaic_symbols.json (direct mapping, not color-guessing). `letters` optionally filters."""
    frames = color_frame_map()                     # char -> frame name
    if letters is not None:
        frames = {ch: fr for ch, fr in frames.items() if ch in letters}
    got = extract_named(cache_dir, list(dict.fromkeys(frames.values())))   # frame -> path
    return {ch: got[fr] for ch, fr in frames.items() if fr in got}

def powerup_icon_map(cache_dir):
    """Extract powerup icons; return tag-char -> path for those present."""
    extracted = extract_named(cache_dir, list(POWERUP_FRAMES.values()))
    return {ch: extracted[name] for ch, name in POWERUP_FRAMES.items() if name in extracted}

def tag_sprite_map(cache_dir, tags=None):
    """Extract the mosaic tag icons declared in mosaic_symbols.json; return tag-char -> png path."""
    import tbmosaic
    tags = tags or tbmosaic.symbols("tags")
    frames = {ch: t["frame"] for ch, t in tags.items() if t.get("frame")}
    got = extract_named(cache_dir, list(frames.values()))
    return {ch: got[fr] for ch, fr in frames.items() if fr in got}
