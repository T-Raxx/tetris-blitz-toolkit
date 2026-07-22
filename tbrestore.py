import json, pathlib
import tbfiles, tbcrypt, tbmods

COEFF = tbmods.COEFF
STATUS_FILE = "restore_status.json"

def _load(name, key):
    return tbfiles.load_path(str(COEFF / name), key)

def _load_status():
    p = pathlib.Path(STATUS_FILE)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def set_status(uId, status):
    d = _load_status(); d[str(uId)] = status
    pathlib.Path(STATUS_FILE).write_text(json.dumps(d, indent=1), encoding="utf-8")

def _base_name(icon):
    icon = icon or ""
    n = icon.split("_", 1)[1] if "_" in icon else icon
    return (n[:1].upper() + n[1:]) if n else "?"

def restore_catalog(key=None):
    key = key or tbcrypt.load_key()
    helpers = _load("helper.json", key).obj["helpers"]
    live_types = {}
    for x in helpers:
        if x.get("active") == 1 and x.get("typeId") is not None:
            live_types.setdefault(x["typeId"], x)
    ov = _load_status()
    out = []
    for x in helpers:
        if x.get("active") == 1:
            continue
        tid = x.get("typeId"); twin = live_types.get(tid)
        if str(x.get("uId")) in ov:
            status = ov[str(x["uId"])]
        elif x.get("uId") == 45:
            status = "crashes"
        elif twin:
            status = "works"
        else:
            status = "untested"
        out.append({"uId": x.get("uId"), "name": x.get("name"), "icon": x.get("iconBasePath"),
            "typeId": tid, "reskin_parent": (twin.get("iconBasePath") if twin else None),
            "status": status, "note": (f"reskin of {twin.get('iconBasePath')}" if twin else "own code")})
    return out

def apply_restore(uIds, stage_dir="mod_stage", key=None):
    key = key or tbcrypt.load_key()
    ids = {int(u) for u in uIds}
    cat = {c["uId"]: c for c in restore_catalog(key)}
    htb = _load("helper.json", key); helper = htb.obj
    crashers = []
    for x in helper["helpers"]:
        if x.get("uId") in ids:
            x["active"] = 1; x["unlockedByDefault"] = True; x["promotion"] = False
            if cat.get(x["uId"], {}).get("status") == "crashes":
                crashers.append(x)
    tbmods.level_fix(helper)
    stage = pathlib.Path(stage_dir) / "assets" / "Assets" / "Coefficients"
    stage.mkdir(parents=True, exist_ok=True)
    (stage / "helper.json").write_bytes(tbfiles.dump_bytes(htb))
    staged = ["helper.json"]
    if crashers:
        lo = _load("LocStringsOverride.json", key); fl = _load("ManualForceLocStringOverride.json", key)
        for x in crashers:
            tbmods.label_crasher(lo.obj, fl.obj, x.get("name"), _base_name(x.get("iconBasePath")))
        (stage / "LocStringsOverride.json").write_bytes(tbfiles.dump_bytes(lo))
        (stage / "ManualForceLocStringOverride.json").write_bytes(tbfiles.dump_bytes(fl))
        staged += ["LocStringsOverride.json", "ManualForceLocStringOverride.json"]
    return {"staged": staged, "restored": sorted(ids), "labeled_crashers": [x.get("uId") for x in crashers]}
