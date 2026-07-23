import json, re, pathlib, plistlib
import tbassets, tbatlas

ASSETS = pathlib.Path("..") / "Tetris blitz" / "assets" / "Assets"
COCOS = ASSETS / "Cocos2dxImages" / "size150"
DEC = pathlib.Path("decrypted")
SO = pathlib.Path("..") / "Tetris blitz" / "lib" / "arm64-v8a" / "libTetrisBlitzApp.so"

EVENT_PATTERNS = ["july", "holiday", "spooky", "halloween", "birthday", "xmas", "christmas",
    "valentine", "amor", "dunkin", "toyota", "dropbox", "flonase", "sponsor", "elfy", "gifting", "bday"]

def _load(name):
    return json.load(open(DEC / name, encoding="utf-8"))

def atlas_index():
    idx = {}
    for pl in COCOS.rglob("*.plist"):
        try:
            d = plistlib.loads(pl.read_bytes())
        except Exception:
            continue
        atlas = pl.with_suffix(".png")
        for full in d.get("frames", {}):
            base = full.split("/")[-1].rsplit(".", 1)[0]
            idx.setdefault(base, (str(pl), str(atlas), full))
    return idx

def reference_tokens():
    refs = set()
    for p in DEC.glob("*.json"):
        refs |= set(re.findall(r"[A-Za-z0-9_]{3,}", p.read_text(encoding="utf-8", errors="ignore")))
    if SO.exists():
        for m in re.findall(rb"[A-Za-z0-9_]{4,}", SO.read_bytes()):
            refs.add(m.decode("latin1"))
    return refs

def detect_disabled_powerups():
    out = []
    try:
        h = _load("helper.json")
    except Exception:
        return out
    for x in h.get("helpers", []):
        active = x.get("active")
        promo = bool(x.get("promotion") or x.get("promo"))
        if active == 1 and not promo and x.get("name"):
            continue
        icon = x.get("iconBasePath") or ""
        out.append({"category": "disabled_powerup", "id": f"helper_{x.get('uId')}",
            "title": x.get("name") or f"(empty slot uId {x.get('uId')})",
            "status": f"active={active}" + (" promo" if promo else ""),
            "source_file": "helper.json", "sprites": [icon] if icon else [],
            "meta": {"uId": x.get("uId"), "active": active, "promo": promo,
                     "price": x.get("price"), "unlockedByDefault": x.get("unlockedByDefault")}})
    return out

def detect_orphan_sprites(index, refs, claimed=()):
    claimed = set(claimed)
    out = []
    for base, (pl, atlas, full) in index.items():
        if base in refs or base in claimed:
            continue
        out.append({"category": "orphan_sprite", "id": f"sprite_{base}", "title": base,
            "status": "orphan candidate", "source_file": pathlib.Path(pl).name,
            "sprites": [base], "meta": {"atlas": pathlib.Path(atlas).name}})
    return out

def detect_unused_modes():
    out = []
    try:
        ks = _load("Killswitches.json")
    except Exception:
        ks = {}
    def emit(k, v):
        out.append({"category": "unused_mode", "id": f"killswitch_{k}", "title": str(k),
            "status": f"killswitch={v}", "source_file": "Killswitches.json", "sprites": [], "meta": {}})
    if isinstance(ks, dict):
        for k, v in ks.items():
            if isinstance(v, (bool, int, str)):
                emit(k, v)
    elif isinstance(ks, list):
        for i, v in enumerate(ks):
            emit(i, v)
    return out

def _match_event(s):
    sl = s.lower()
    return next((p for p in EVENT_PATTERNS if p in sl), None)

def detect_event_branded(index):
    out = []
    try:
        h = _load("helper.json")
    except Exception:
        h = {"helpers": []}
    for x in h.get("helpers", []):
        p = _match_event(f"{x.get('name','')} {x.get('iconBasePath','')}")
        if p:
            icon = x.get("iconBasePath") or ""
            out.append({"category": "event_branded", "id": f"event_helper_{x.get('uId')}",
                "title": x.get("name") or icon, "status": f"event/brand: {p}",
                "source_file": "helper.json", "sprites": [icon] if icon else [],
                "meta": {"uId": x.get("uId"), "pattern": p}})
    for f in DEC.glob("*.json"):
        p = _match_event(f.stem)
        if p:
            out.append({"category": "event_branded", "id": f"event_file_{f.stem}", "title": f.name,
                "status": f"event/brand: {p}", "source_file": f.name, "sprites": [], "meta": {"pattern": p}})
    for base, (pl, atlas, full) in index.items():
        p = _match_event(base)
        if p:
            out.append({"category": "event_branded", "id": f"event_sprite_{base}", "title": base,
                "status": f"event/brand: {p}", "source_file": pathlib.Path(pl).name,
                "sprites": [base], "meta": {"pattern": p}})
    return out

def _counts(findings):
    c = {}
    for f in findings:
        c[f["category"]] = c.get(f["category"], 0) + 1
    return c

def detect_db_assets(cache_dir, assets_dir=tbatlas.ASSETS):
    cache = pathlib.Path(cache_dir) / "thumbnails"; cache.mkdir(parents=True, exist_ok=True)
    out = []
    for db in tbatlas.list_db_banks(assets_dir):
        data = db.read_bytes()
        try:
            frames = tbatlas.parse_frames(data); atlas = tbatlas.atlas_image(data)
        except Exception:
            continue
        stem = db.stem
        for name, (x, y, w, h) in frames.items():
            thumb = cache / f"db_{stem}_{name}.png"
            atlas.crop((x, y, x + w, y + h)).save(thumb)
            out.append({"category": "db_asset", "id": f"db_{stem}_{name}", "title": name,
                        "status": "packed", "source_file": db.name,
                        "sprites": [name], "thumbs": [str(thumb)]})
    return out

def build_catalog(cache_dir="discovery_cache", include_db=True):
    cache = pathlib.Path(cache_dir); (cache / "thumbnails").mkdir(parents=True, exist_ok=True)
    idx = atlas_index(); refs = reference_tokens()
    disabled = detect_disabled_powerups()
    events = detect_event_branded(idx)
    modes = detect_unused_modes()
    claimed = {s for f in (disabled + events) for s in f["sprites"]}
    orphans = detect_orphan_sprites(idx, refs, claimed)
    findings = disabled + events + modes + orphans

    want = {}
    for f in findings:
        for s in f["sprites"]:
            b = s.split("/")[-1]
            if b in idx:
                want[b] = idx[b]
    by_atlas = {}
    for b, (pl, atlas, full) in want.items():
        by_atlas.setdefault((pl, atlas), []).append(full)
    thumb = {}
    for (pl, atlas), names in by_atlas.items():
        try:
            got = tbassets.extract_named(str(cache / "thumbnails"), names, plist=pl, atlas=atlas)
        except Exception:
            got = {}
        for full, path in got.items():
            thumb[full.split("/")[-1].rsplit(".", 1)[0]] = path
    for f in findings:
        f["thumbs"] = [thumb[s.split("/")[-1]] for s in f["sprites"] if s.split("/")[-1] in thumb]

    if include_db:
        findings = findings + detect_db_assets(cache_dir)
    catalog = {"counts": _counts(findings), "findings": findings}
    (cache / "catalog.json").write_text(json.dumps(catalog, indent=1), encoding="utf-8")
    return catalog
