import pathlib, pytest
import tbsave, tbcrypt, tbfiles

pytestmark = pytest.mark.skipif(not (tbsave.BASE_DIR / "PlayerData.json").exists(),
                                reason="Samsung save base not present")
KEY = tbcrypt.load_key("key.json")

def _base():
    return tbsave.load_base(key=KEY)

def test_load_base_and_summary():
    base = _base()
    assert "PlayerData.json" in base and "NarcSave.json" in base
    s = tbsave.summary(tbsave.playerdata(base))
    assert s["coins"] and s["level"] == 193 and s["unlocks"] >= 71

def test_set_currency_only_known_fields():
    pd = tbsave.playerdata(_base())
    tbsave.set_currency(pd, Coins=tbsave.MAXINT, PremiumCoins=5000, Bogus=1)
    assert pd["Coins"] == tbsave.MAXINT and pd["PremiumCoins"] == 5000
    assert "Bogus" not in pd

def test_unlock_all_adds_missing_without_dupes():
    base = _base(); pd = tbsave.playerdata(base)
    before = {u["Id"] for u in pd["Unlocks"]}
    helper = tbsave._load_coeff("helper.json", KEY)
    leveling = tbsave._load_coeff("LevelingAwards.json", KEY)
    tbsave.unlock_all_in_save(pd, helper, leveling)
    after_ids = [u["Id"] for u in pd["Unlocks"]]
    assert len(after_ids) == len(set(after_ids))                 # no dupes
    want = tbsave.all_unlock_ids(helper, leveling)
    assert want <= set(after_ids)                                # every unlock present
    assert 18 in after_ids and 18 not in before                  # a cut powerup got added

def test_max_helpers_all_owned_level5():
    base = _base(); pd = tbsave.playerdata(base)
    helper = tbsave._load_coeff("helper.json", KEY)
    n_helpers = len(tbsave._helpers(helper))
    tbsave.max_helpers(pd, helper, level=5)
    inv = {h["Id"]: h for h in pd["HelperInventory"]}
    assert len(inv) >= n_helpers
    assert all(h["Level"] == 5 for h in pd["HelperInventory"])

def test_apply_mods_and_stage_roundtrips(tmp_path):
    base = _base()
    tbsave.apply_mods(base, {"currency": {"Coins": 999}, "unlock_all": True, "max_helpers": True}, key=KEY)
    written = tbsave.stage_modded(base, tmp_path, key=KEY)
    assert any("PlayerData.json" in w for w in written)
    reloaded = tbfiles.load_path(str(tmp_path / "PlayerData.json"), KEY).obj
    assert reloaded["Coins"] == 999
    assert 18 in {u["Id"] for u in reloaded["Unlocks"]}          # unlock persisted through re-encrypt

def test_narcsave_preserved_byte_identical(tmp_path):
    base = _base()
    tbsave.apply_mods(base, {"currency": {"Coins": 1}}, key=KEY)  # only PlayerData touched
    tbsave.stage_modded(base, tmp_path, key=KEY)
    orig = (tbsave.BASE_DIR / "NarcSave.json").read_bytes()
    staged = (tmp_path / "NarcSave.json").read_bytes()
    assert staged == orig                                        # NarcSave untouched, byte-identical
