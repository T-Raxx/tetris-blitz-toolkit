"""Nivel 3 — mino texture injection (pixel-inject over a base-color frame in Common0.png).

The mosaic renderer resolves a color enum -> a Common-atlas sprite frame; the char->enum
loader is unlocated and the switch is compiled, so we can't wire NEW chars. Instead we
overwrite the PIXELS of a base color's frame in Common0.png with any source image (a real
hidden game texture, or a custom PNG). That color char then renders the injected art
in-game AND in finisher matrices. Pure asset mod (mod_stage), reversible, no native patch.
"""
import pathlib, plistlib, re
from PIL import Image
import tbassets

ASSETS = tbassets.ASSETS
COMMON_PNG = tbassets.ATLAS                       # size150/Common/Common0.png
COMMON_PLIST = tbassets.PLIST                     # size150/Common/Common0.plist
COMMON_REL = "assets/Assets/Cocos2dxImages/size150/Common/Common0.png"

def base_targets():
    """char -> Common frame name of the base color it paints (the sacrificeable slots)."""
    return tbassets.color_frame_map()

def _frames(plist=COMMON_PLIST):
    return plistlib.loads(pathlib.Path(plist).read_bytes())["frames"]

def frame_rect(frame_name, plist=COMMON_PLIST):
    """(x, y, w, h, rotated) for a Common frame; raises KeyError if absent."""
    meta = _frames(plist)[frame_name]
    x, y, w, h = tbassets._nums(meta.get("frame") or meta.get("textureRect"))[:4]
    rot = bool(meta.get("rotated") or meta.get("textureRotated"))
    return x, y, w, h, rot

def fit_into(src, w, h):
    """RGBA (w,h) canvas with `src` scaled to fit (aspect-preserved) and centered."""
    src = src.convert("RGBA")
    if src.width == 0 or src.height == 0:
        return Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ratio = min(w / src.width, h / src.height)
    nw, nh = max(1, round(src.width * ratio)), max(1, round(src.height * ratio))
    scaled = src.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.paste(scaled, ((w - nw) // 2, (h - nh) // 2))
    return canvas

def inject_over(atlas_img, base_frame, source_img, plist=COMMON_PLIST):
    """Paste `source_img` (scaled to the frame rect) over `base_frame`'s region in `atlas_img`
    (mutates + returns it). Fully replaces the region incl. alpha, so old pixels are gone."""
    x, y, w, h, rot = frame_rect(base_frame, plist)
    if rot:
        canvas = fit_into(source_img, h, w).transpose(Image.ROTATE_270)   # atlas stores rotated
        atlas_img.paste(canvas, (x, y))
    else:
        atlas_img.paste(fit_into(source_img, w, h), (x, y))
    return atlas_img

def _resolve_base(base, targets=None):
    """Accept a color char ('n') or a full frame name; return the Common frame name."""
    targets = targets or base_targets()
    if base in targets:                # a color char
        return targets[base]
    return base                        # already a frame name

def stage_injections(injections, stage_dir="mod_stage", common_png=COMMON_PNG, plist=COMMON_PLIST):
    """injections = [{"base": char|frame, "source": png_path}]. Applies every paste onto one
    copy of Common0.png and writes it into the mod stage. Returns {staged, applied}."""
    if not injections:
        return {"staged": [], "applied": []}
    atlas = Image.open(common_png).convert("RGBA")
    targets = base_targets(); applied = []
    for inj in injections:
        base_frame = _resolve_base(inj["base"], targets)
        src = Image.open(inj["source"]).convert("RGBA")
        inject_over(atlas, base_frame, src, plist)
        applied.append(f"inject:{inj['base']}<-{pathlib.Path(inj['source']).stem}")
    dest = pathlib.Path(stage_dir) / COMMON_REL
    dest.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(dest)
    return {"staged": [COMMON_REL], "applied": applied}

# --- catalog of real hidden mino/effect textures usable as injection sources ---------------
# kind: "common" (a frame in Common0), "loose" (a standalone PNG under assets), "atlas" (frame
# inside another cocos plist+png), "db" (frame inside a QFS .db bank).
CATALOG = {
    "Pink mino":       ("db", "imagesSize150_GameCommonAlpha.db", r"[Pp]ink"),
    "Bday cake":       ("atlas", "Cocos2dxImages/size150/Scene_Game/PowerUps/BDay421/BDay4210",
                        r"Bday421Full(?!2)"),
    "Popcorn":         ("loose", "Static/finisher_popcorn.png"),
    "Bulldozer":       ("loose", "Static/vfx_bulldozer.png"),
    "Frenzy garbage":  ("common", "Common/garbageStratas00Single.png"),
    "Gold cube":       ("common", "Common/MinoCubeYellow.png"),
    "White cube":      ("common", "Common/MinoCubeWhite.png"),
    "Frostbite ice":   ("db", "imagesSize150_GamePowerupsFrostBite.db", r"frostbite_ice"),
    "Mino shards":     ("common", "Common/MinoShards.png"),
}

def _extract_atlas_frame(base, cache_dir, regex):
    """Extract the first frame matching `regex` from a cocos plist+png pair -> png path."""
    plist = ASSETS / (base + ".plist"); png = ASSETS / (base + ".png")
    if not plist.exists():
        return None
    frames = plistlib.loads(plist.read_bytes())["frames"]
    hit = next((k for k in frames if re.search(regex, k)), None)
    if not hit:
        return None
    return tbassets.extract_named(cache_dir, [hit], plist=plist, atlas=png).get(hit)

def _extract_db_frame(bank, cache_dir, regex):
    import tbatlas
    b = ASSETS / bank
    if not b.exists():
        return None
    try:
        frames = tbatlas.parse_frames(b.read_bytes())
    except Exception:
        return None
    hit = next((k for k in frames if re.search(regex, k)), None)
    if not hit:
        return None
    got = tbatlas.extract_db(str(b), cache_dir, rename={hit: re.sub(r"[^A-Za-z0-9_.-]", "_", hit)})
    # extract_db returns {out_name: path}; find ours
    key = re.sub(r"[^A-Za-z0-9_.-]", "_", hit)
    return got.get(key) or next((p for n, p in got.items() if re.search(regex, n)), None)

def catalog_sources(cache_dir="assets_cache"):
    """Resolve every CATALOG entry it can to an extracted PNG path. {label: path} (skips misses)."""
    out = {}
    for label, spec in CATALOG.items():
        kind = spec[0]
        try:
            if kind == "common":
                got = tbassets.extract_named(cache_dir, [spec[1]])
                p = got.get(spec[1])
            elif kind == "loose":
                p = str(ASSETS / spec[1]) if (ASSETS / spec[1]).exists() else None
            elif kind == "atlas":
                p = _extract_atlas_frame(spec[1], cache_dir, spec[2])
            elif kind == "db":
                p = _extract_db_frame(spec[1], cache_dir, spec[2])
            else:
                p = None
        except Exception:
            p = None
        if p:
            out[label] = p
    return out
