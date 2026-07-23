import tbmods

def _helper():
    return {"helpers": [
        {"uId": 38, "typeId": 31, "active": 1, "params": {"NumMinos": 12},
         "perks": [{"Level": 1, "Effects": {"Active": [{"name": "X", "value": 1}]}}]},
        {"uId": 45, "typeId": 37, "active": 2, "promotion": True, "price": 6000,
         "params": {"numMinos": 12, "vortexFadeInTime": 750}, "numFreePOWUses": 5},
    ]}

def test_fix_flonase_reroutes_typeid_and_fixes_param():
    h = _helper()
    tbmods.fix_flonase(h)
    fl = next(x for x in h["helpers"] if x["uId"] == 45)
    assert fl["typeId"] == 31                 # rerouted to Mino Vortex's working effect
    assert "NumMinos" in fl["params"]         # param casing fixed
    assert "numMinos" not in fl["params"]
    assert fl["params"]["NumMinos"] == 12
    assert fl["active"] == 1 and fl["unlockedByDefault"] is True
    assert fl["perks"]                        # inherited Mino Vortex perks
    assert fl["price"] == 0

def test_apply_and_stage_flag(tmp_path):
    # config plumbing: fix_flonase reaches apply_and_stage.applied
    out = tbmods.apply_and_stage({"fix_flonase": True}, stage_dir=str(tmp_path))
    assert "fix_flonase" in out["applied"]
    assert "helper.json" in out["staged"]
