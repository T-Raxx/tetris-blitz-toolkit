import json, pathlib, re

SEM_FILE = "semantics.json"

CORE_CHEATS = [
    {"key": "GameTimeInMs",       "label": "Game duration (ms)",   "note": "blitz timer; 120000 = 2 min"},
    {"key": "GravityDeltaTimeMs", "label": "Gravity delay (ms)",   "note": "higher = slower fall"},
    {"key": "DropSpeed",          "label": "Drop speed",           "note": ""},
    {"key": "LockTimeMs",         "label": "Lock delay (ms)",      "note": "grace before a piece locks"},
    {"key": "FrenzySize",         "label": "Frenzy size",          "note": ""},
    {"key": "FrenzyGarbageRows",  "label": "Frenzy garbage rows",  "note": ""},
    {"key": "SpawnRow",           "label": "Spawn row",            "note": ""},
    {"key": "RegularCascadeSize", "label": "Regular cascade size", "note": ""},
    {"key": "MegaCascadeSize",    "label": "Mega cascade size",    "note": ""},
    {"key": "UltraCascadeSize",   "label": "Ultra cascade size",   "note": ""},
]

_cache = None

def load_curated(path=SEM_FILE):
    global _cache
    if _cache is None:
        p = pathlib.Path(path)
        _cache = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return _cache

_COLOUR = re.compile(r"Colou?r([RGB])$")

def _humanize(s):
    hint = None
    if s.startswith("BYTE_"):
        hint, s = "byte(0-255)", s[5:]
    elif s.startswith("INT_"):
        hint, s = "int", s[4:]
    suffix = ""
    m = _COLOUR.search(s)
    if m:
        suffix = f" ({m.group(1)})"; s = s[:m.start()] + "Colour"
    elif s.endswith("Ms"):
        suffix = " (ms)"; s = s[:-2]
    words = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", s).replace("_", " ").split()
    label = (" ".join(w[:1].upper() + w[1:] for w in words) + suffix).strip()
    return label or s, hint

def describe(key, powerup=None):
    cur = load_curated()
    for k in ((f"{powerup}|{key}" if powerup else None), f"|{key}"):
        if k and k in cur:
            e = cur[k]
            return {"label": e["label"], "tooltip": e.get("tooltip", key), "hint": None}
    label, hint = _humanize(key)
    return {"label": label or key, "tooltip": key, "hint": hint}
