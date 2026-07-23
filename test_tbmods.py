import json, pathlib, copy
import tbmods, tbfiles, tbcrypt

KEY = tbcrypt.load_key("key.json")
COEFF = pathlib.Path("..") / "Tetris blitz" / "assets" / "Assets" / "Coefficients"

def _obj(name):
    return tbfiles.load_path(str(COEFF / name), KEY).obj

def test_unlock_all():
    h = _obj("helper.json"); tbmods.unlock_all_powerups(h)
    assert all(x["active"] == 1 and x["unlockedByDefault"] for x in h["helpers"])

def test_show_hidden_and_level_fix_flonase():
    h = _obj("helper.json"); tbmods.show_hidden_powerups(h)
    by = {x["uId"]: x for x in h["helpers"]}
    assert by[45]["active"] == 1
    assert len(by[45]["perks"]) > 0

def test_behavior_laser_clear_whole_matrix():
    h = _obj("helper.json")
    tbmods.set_powerup_behavior(h, 2, preset="clear_whole_matrix")
    by = {x["uId"]: x for x in h["helpers"]}
    assert by[2]["params"]["NumLineClears"] == 20
    vals = [e["value"] for p in by[2]["perks"] for e in p.get("Effects", {}).get("Active", [])
            if e.get("param") == "NumLineClears"]
    assert vals and all(v == 20 for v in vals)

def test_set_currency():
    pd = _obj("PlayerData.json")
    tbmods.set_currency(pd, coins=999999, level=50)
    assert pd["Coins"] == 999999 and pd["LevelData"]["Level"] == 50

def test_level_fix_inherits_typeid_twin_perks():
    h = _obj("helper.json")
    by = {x["uId"]: x for x in h["helpers"]}
    laser_perks = len(by[2]["perks"])
    by[24]["active"] = 1                          # restore Toyota finisher (typeId 3 = Laser)
    tbmods.level_fix(h)
    assert len(by[24]["perks"]) == laser_perks    # inherited Laser's perks

def test_label_crasher_generic():
    lo = _obj("LocStringsOverride.json"); fl = _obj("ManualForceLocStringOverride.json")
    tbmods.label_crasher(lo, fl, "STRID_HELPERS_WILDCARD_TITLE", "WildCard")
    hit = [s for s in lo["strings"] if s["key"] == "STRID_HELPERS_WILDCARD_TITLE"]
    assert hit and hit[0]["text"]["en"] == "WildCard (CRASHES GAME)"
    assert "STRID_HELPERS_WILDCARD_TITLE" in fl["strings"]

def test_apply_and_stage_roundtrips(tmp_path):
    cfg = {"unlock_all": True, "currency": {"on": True, "coins": 12345},
           "behavior": [{"uId": 2, "preset": "clear_whole_matrix"}]}
    res = tbmods.apply_and_stage(cfg, str(tmp_path / "stage"), KEY)
    assert "helper.json" in res["staged"] and "PlayerData.json" in res["staged"]
    stage = tmp_path / "stage" / "assets" / "Assets" / "Coefficients"
    h = tbfiles.load_bytes((stage / "helper.json").read_bytes(), KEY).obj
    by = {x["uId"]: x for x in h["helpers"]}
    assert by[2]["params"]["NumLineClears"] == 20 and by[2]["active"] == 1
    pd = tbfiles.load_bytes((stage / "PlayerData.json").read_bytes(), KEY).obj
    assert pd["Coins"] == 12345
