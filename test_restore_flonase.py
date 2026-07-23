import pathlib, tbmods

def test_enable_flonase_keeps_typeid37():
    h = {"helpers": [
        {"uId": 38, "typeId": 31, "perks": [{"Level": 1}]},
        {"uId": 45, "typeId": 37, "active": 2, "promotion": True, "price": 6000, "numFreePOWUses": 5}]}
    tbmods.enable_flonase(h)
    fl = next(x for x in h["helpers"] if x["uId"] == 45)
    assert fl["typeId"] == 37 and fl["active"] == 1 and fl["price"] == 0
    assert fl["unlockedByDefault"] is True and fl["perks"]

def test_restore_flonase_assets(tmp_path):
    staged = tbmods.restore_flonase_assets(str(tmp_path))
    scene = tmp_path / "assets" / "Assets" / "CocosScenes" / "Scene_Flonace"
    for n in ["flonase_Bottle_idle.png", "flonase_Banner.png", "flonase_PU_vfx1.png"]:
        assert (scene / n).exists(), n

def test_apply_and_stage_restore_flonase(tmp_path):
    out = tbmods.apply_and_stage({"restore_flonase": True}, stage_dir=str(tmp_path))
    assert "restore_flonase" in out["applied"]
    assert "helper.json" in out["staged"]
