"""Samsung save as patch base — load the user's genuine PlayerData+NarcSave (event content
unlocked, Level 193 grandfathered, 742M coins) and apply coherent mods on top, then export /
push. NarcSave is preserved as-is (consistent with PlayerData). Level/XP is NOT modified here
(open question — the game recomputes it; see docs/mino_re.md / leveling RE)."""
import os, pathlib, tbfiles, tbcrypt

# Directory holding your device save files (PlayerData.json, NarcSave.json, ...).
# Set TB_SAVE_DIR to point at your own pulled save; defaults to ./save next to the repo.
BASE_DIR = pathlib.Path(os.environ.get("TB_SAVE_DIR", "save"))
COEF_DIR = pathlib.Path("..") / "Tetris blitz" / "assets" / "Assets" / "Coefficients"
SAVE_FILES = ["PlayerData.json", "NarcSave.json", "BonusBoards.json",
              "DeviceSettings.json", "LocalFileHash.json"]
CURRENCY = ["Coins", "PremiumCoins", "PremiumShards", "GrindShards", "SkillShards",
            "Spins", "GoldRushGames", "Energy"]
MAXINT = 2_000_000_000

def load_base(base_dir=BASE_DIR, key=None):
    """{filename: TbFile} for every save file present in base_dir."""
    key = key or tbcrypt.load_key("key.json")
    base_dir = pathlib.Path(base_dir)
    return {f: tbfiles.load_path(str(base_dir / f), key)
            for f in SAVE_FILES if (base_dir / f).exists()}

def playerdata(base):
    return base["PlayerData.json"].obj

def summary(pd):
    ld = pd.get("LevelData", {}) or {}
    return {"coins": pd.get("Coins"), "premium": pd.get("PremiumCoins"),
            "shards": pd.get("PremiumShards"), "spins": pd.get("Spins"),
            "level": ld.get("Level"), "xp": pd.get("XP"),
            "unlocks": len(pd.get("Unlocks", [])), "helpers": len(pd.get("HelperInventory", []))}

def set_currency(pd, **vals):
    """Set any of CURRENCY fields (skip None). Returns pd."""
    for k, v in vals.items():
        if v is not None and k in CURRENCY:
            pd[k] = int(v)
    return pd

def _load_coeff(name, key):
    return tbfiles.load_path(str(COEF_DIR / name), key).obj

def _helpers(helper):
    return helper.get("helpers", []) if isinstance(helper, dict) else helper

def all_unlock_ids(helper, leveling):
    """Every uId that can be an unlock: all helper uIds + LevelingAwards unlock/finisher rewards."""
    ids = set()
    for h in _helpers(helper):
        u = h.get("uId", h.get("Id"))
        if isinstance(u, int):
            ids.add(u)
    for lv in (leveling.get("levels", []) if isinstance(leveling, dict) else []):
        for r in lv.get("rewards", []):
            if r.get("type") in ("unlock", "finisher") and isinstance(r.get("uId"), int):
                ids.add(r["uId"])
    return ids

def unlock_all_in_save(pd, helper, leveling):
    """Add every unlock id missing from PlayerData.Unlocks[] (genuine save unlock, not free-coeff)."""
    have = {u.get("Id") for u in pd.setdefault("Unlocks", [])}
    for i in sorted(all_unlock_ids(helper, leveling)):
        if i not in have:
            pd["Unlocks"].append({"Id": i}); have.add(i)
    return pd

def max_helpers(pd, helper, level=5, quantity=99):
    """Every helper owned at `level` with >= `quantity` (maxes existing + adds missing entries)."""
    inv = pd.setdefault("HelperInventory", [])
    have = {}
    for h in inv:                                     # max every entry already owned
        h["Level"] = level
        h["Quantity"] = max(h.get("Quantity", 0), quantity)
        have[h["Id"]] = h
    for h in _helpers(helper):                        # add any helper not yet owned
        uid = h.get("uId", h.get("Id"))
        if isinstance(uid, int) and uid not in have:
            entry = {"Id": uid, "Quantity": quantity, "Level": level}
            inv.append(entry); have[uid] = entry
    return pd

def apply_mods(base, mods, key=None):
    """mods = {currency:{...}, unlock_all:bool, max_helpers:bool, helper_level:int}. Mutates base."""
    key = key or tbcrypt.load_key("key.json")
    pd = playerdata(base)
    if mods.get("currency"):
        set_currency(pd, **mods["currency"])
    if mods.get("unlock_all") or mods.get("max_helpers"):
        helper = _load_coeff("helper.json", key)
        leveling = _load_coeff("LevelingAwards.json", key)
        if mods.get("unlock_all"):
            unlock_all_in_save(pd, helper, leveling)
        if mods.get("max_helpers"):
            max_helpers(pd, helper, level=mods.get("helper_level", 5))
    return base

def stage_modded(base, out_dir, key=None):
    """Re-encrypt every save file (with any obj edits) into out_dir. Returns list of written paths."""
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    written = []
    for fname, tb in base.items():
        p = out / fname
        p.write_bytes(tbfiles.dump_bytes(tb))
        written.append(str(p))
    return written

def push_to_device(base, key=None, run=None):
    """Push modded PlayerData+NarcSave to the device (auto-backs up device save). rooted/adb-dev only."""
    import tbadb
    kwargs = {"run": run} if run else {}
    backups = []
    for fname in ("PlayerData.json", "NarcSave.json"):
        if fname in base:
            data = tbfiles.dump_bytes(base[fname])
            backups.append(tbadb.push(f"{tbadb.FILES_DIR}/{fname}", data, **kwargs))
    return {"pushed": [f for f in ("PlayerData.json", "NarcSave.json") if f in base], "backups": backups}
