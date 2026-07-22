import tbmods

def test_set_core_mechanics_sets_known_skips_unknown():
    core = {"GameTimeInMs": 120000, "DropSpeed": 1}
    tbmods.set_core_mechanics(core, {"GameTimeInMs": 300000, "Nope": 5})
    assert core["GameTimeInMs"] == 300000
    assert core["DropSpeed"] == 1
    assert "Nope" not in core

def test_apply_and_stage_core_mechanics(tmp_path):
    out = tbmods.apply_and_stage({"core_mechanics": {"GameTimeInMs": 300000}},
                                 stage_dir=str(tmp_path))
    assert "core_mechanics" in out["applied"]
    assert "CoreMechanicsCoefficients.json" in out["staged"]
    import tbfiles, tbcrypt
    staged = tmp_path / "assets" / "Assets" / "Coefficients" / "CoreMechanicsCoefficients.json"
    tb = tbfiles.load_bytes(staged.read_bytes(), tbcrypt.load_key())
    assert tb.obj["GameTimeInMs"] == 300000
