import copy, pathlib
import tbfiles, tbcrypt

COEFF = pathlib.Path("..") / "Tetris blitz" / "assets" / "Assets" / "Coefficients"

def _load(name, key):
    return tbfiles.load_path(str(COEFF / name), key)

def POWERUPS(key=None):
    key = key or tbcrypt.load_key()
    return _load("helper.json", key).obj["helpers"]

def unlock_all_powerups(helper):
    for x in helper["helpers"]:
        x["active"] = 1; x["unlockedByDefault"] = True

def level_fix(helper):
    perks_by_type = {}
    for x in helper["helpers"]:
        if x.get("perks") and x.get("typeId") is not None:
            perks_by_type.setdefault(x["typeId"], x["perks"])
    mv = next((x["perks"] for x in helper["helpers"] if x.get("uId") == 38 and x.get("perks")), [])
    stub = [{"Level": 1, "Upgrade": {"Cost": 0, "LevelGate": -1, "PUatLevelGate": -1},
             "Effects": {"Active": []}}]
    for x in helper["helpers"]:
        if x.get("active") == 1 and not x.get("perks"):
            tid = x.get("typeId")
            if tid in perks_by_type:
                x["perks"] = copy.deepcopy(perks_by_type[tid])
            elif x.get("uId") == 45 and mv:
                x["perks"] = copy.deepcopy(mv)
            else:
                x["perks"] = copy.deepcopy(stub)

def fix_flonase(helper, src_uId=38, dst_uId=45):
    """Reroute Flonase (uId45, typeId37) to Mino Vortex's working NEW vortex effect (typeId31).
    typeId37 dispatches to the deprecated/broken OLD vortex effect (reads 'numMinos'); typeId31 to the
    finished NEW effect (reads 'NumMinos'). Fix param casing, copy Mino Vortex perks, enable + free."""
    by = {x.get("uId"): x for x in helper["helpers"]}
    dst = by.get(dst_uId); src = by.get(src_uId)
    if not dst or not src:
        return
    dst["typeId"] = src.get("typeId")
    params = dst.get("params")
    if isinstance(params, dict) and "numMinos" in params and "NumMinos" not in params:
        params["NumMinos"] = params.pop("numMinos")
    if not dst.get("perks") and src.get("perks"):
        dst["perks"] = copy.deepcopy(src["perks"])
    dst["active"] = 1; dst["unlockedByDefault"] = True; dst["promotion"] = False
    dst["price"] = 0
    for k in ("numFreeUses", "numFreePOWUses", "numFreePurchaseUses"):
        if k in dst:
            dst[k] = 99

def show_hidden_powerups(helper):
    for x in helper["helpers"]:
        if x.get("active") != 1:
            x["active"] = 1; x["unlockedByDefault"] = True; x["promotion"] = False
    level_fix(helper)

def all_powerups_free(helper):
    for x in helper["helpers"]:
        x["price"] = 0
        for k in ("numFreeUses", "numFreePOWUses", "numFreePurchaseUses"):
            if k in x:
                x[k] = 99

def set_currency(playerdata, coins=None, premium=None, shards=None, spins=None, level=None, xp=None):
    for k, v in {"Coins": coins, "PremiumCoins": premium, "Spins": spins, "XP": xp}.items():
        if v is not None and k in playerdata:
            playerdata[k] = v
    if shards is not None:
        for k in ("PremiumShards", "GrindShards", "SkillShards"):
            if k in playerdata:
                playerdata[k] = shards
    if level is not None and isinstance(playerdata.get("LevelData"), dict):
        playerdata["LevelData"]["Level"] = level

def set_powerup_behavior(helper, uId, param_overrides=None, perk_value_overrides=None, preset=None):
    by = {x["uId"]: x for x in helper["helpers"]}
    pu = by.get(uId)
    if not pu:
        return
    params = dict(param_overrides or {})
    if preset == "clear_whole_matrix":
        params["NumLineClears"] = 20
    if preset == "free_unlock":
        pu["price"] = 0; pu["unlockedByDefault"] = True; pu["active"] = 1
    if isinstance(pu.get("params"), dict):
        for k, v in params.items():
            pu["params"][k] = v
    for k, v in params.items():
        if isinstance(v, (int, float)):
            for perk in pu.get("perks", []):
                for eff in perk.get("Effects", {}).get("Active", []):
                    if eff.get("param") == k:
                        eff["value"] = v
    if preset == "max_perks":
        for perk in pu.get("perks", []):
            up = perk.setdefault("Upgrade", {})
            up["Cost"] = 0; up["LevelGate"] = -1; up["PUatLevelGate"] = -1
    for lvl, val in (perk_value_overrides or {}).items():
        for perk in pu.get("perks", []):
            if perk.get("Level") == int(lvl):
                for eff in perk.get("Effects", {}).get("Active", []):
                    eff["value"] = val

def boost_coin_awards(gameplay, multiplier):
    for k, v in list(gameplay.items()):
        if k.startswith("NumberOfCoinsFor") and isinstance(v, int):
            gameplay[k] = int(v * multiplier)

def set_core_mechanics(core, overrides):
    for k, v in (overrides or {}).items():
        if k in core:
            core[k] = v

def label_crasher(locoverride, forcelist, strid, base_name):
    langs = ["en", "es", "de", "fr", "it", "ja", "ko", "pt", "ru", "zh"]
    text = {l: f"{base_name} (CRASHES GAME)" for l in langs}
    entry = next((s for s in locoverride.get("strings", []) if s.get("key") == strid), None)
    if entry:
        entry["text"] = text
    else:
        locoverride.setdefault("strings", []).append({"key": strid, "text": text})
    if strid not in forcelist.get("strings", []):
        forcelist.setdefault("strings", []).append(strid)

def rename_flonase_crashes(locoverride, forcelist):
    label_crasher(locoverride, forcelist, "STRID_HELPERS_FLONASEPOWERUP_TITLE", "Flonase")

def apply_and_stage(config, stage_dir="mod_stage", key=None):
    key = key or tbcrypt.load_key()
    stage = pathlib.Path(stage_dir) / "assets" / "Assets" / "Coefficients"
    stage.mkdir(parents=True, exist_ok=True)
    touched = {}
    def get(name):
        if name not in touched:
            touched[name] = _load(name, key)
        return touched[name]
    applied = []
    if config.get("unlock_all"):
        unlock_all_powerups(get("helper.json").obj); applied.append("unlock_all")
    if config.get("show_hidden"):
        show_hidden_powerups(get("helper.json").obj); applied.append("show_hidden")
    if config.get("all_free"):
        all_powerups_free(get("helper.json").obj); applied.append("all_free")
    if config.get("fix_flonase"):
        fix_flonase(get("helper.json").obj); applied.append("fix_flonase")
    for b in config.get("behavior", []):
        set_powerup_behavior(get("helper.json").obj, b["uId"], b.get("params"),
                             b.get("perk_values"), b.get("preset"))
        applied.append(f"behavior_{b['uId']}")
    cur = config.get("currency")
    if cur and cur.get("on"):
        set_currency(get("PlayerData.json").obj, cur.get("coins"), cur.get("premium"),
                     cur.get("shards"), cur.get("spins"), cur.get("level"), cur.get("xp"))
        applied.append("currency")
    ca = config.get("coin_awards")
    if ca and ca.get("on"):
        boost_coin_awards(get("GameplayCoefficients.json").obj, ca.get("multiplier", 1))
        applied.append("coin_awards")
    cm = config.get("core_mechanics")
    if cm:
        set_core_mechanics(get("CoreMechanicsCoefficients.json").obj, cm)
        applied.append("core_mechanics")
    if config.get("rename_flonase"):
        rename_flonase_crashes(get("LocStringsOverride.json").obj,
                               get("ManualForceLocStringOverride.json").obj)
        applied.append("rename_flonase")
    staged = []
    for name, tb in touched.items():
        (stage / name).write_bytes(tbfiles.dump_bytes(tb)); staged.append(name)
    return {"staged": staged, "applied": applied}
