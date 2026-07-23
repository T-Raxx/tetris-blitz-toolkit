import json, pathlib
import tbrestore, tbfiles, tbcrypt

KEY = tbcrypt.load_key("key.json")
COEFF = pathlib.Path("..") / "Tetris blitz" / "assets" / "Assets" / "Coefficients"

def test_catalog_status_seed(tmp_path, monkeypatch):
    monkeypatch.setattr(tbrestore, "STATUS_FILE", str(tmp_path / "s.json"))  # isolate persisted overrides
    cat = {c["uId"]: c for c in tbrestore.restore_catalog(KEY)}
    assert cat[24]["status"] == "works" and cat[24]["reskin_parent"]   # Toyota (Laser twin)
    assert cat[45]["status"] == "untested"                             # Flonase (own code, restorable)
    assert 2 not in cat                                                # live powerups excluded

def test_set_status_persists(tmp_path, monkeypatch):
    monkeypatch.setattr(tbrestore, "STATUS_FILE", str(tmp_path / "s.json"))
    tbrestore.set_status(31, "works")
    cat = {c["uId"]: c for c in tbrestore.restore_catalog(KEY)}
    assert cat[31]["status"] == "works"

def test_apply_restore_working_pair(tmp_path):
    res = tbrestore.apply_restore([24, 26], str(tmp_path / "stage"), KEY)
    assert res["labeled_crashers"] == []
    stage = tmp_path / "stage" / "assets" / "Assets" / "Coefficients"
    h = tbfiles.load_bytes((stage / "helper.json").read_bytes(), KEY).obj
    by = {x["uId"]: x for x in h["helpers"]}
    assert by[24]["active"] == 1 and len(by[24]["perks"]) > 0
    assert by[26]["active"] == 1 and len(by[26]["perks"]) > 0

def test_apply_restore_labels_crash_on_status_override(tmp_path, monkeypatch):
    monkeypatch.setattr(tbrestore, "STATUS_FILE", str(tmp_path / "s.json"))
    tbrestore.set_status(45, "crashes")            # generic crasher-labeling still works via override
    res = tbrestore.apply_restore([45], str(tmp_path / "stage"), KEY)
    assert 45 in res["labeled_crashers"]

def test_base_name():
    assert tbrestore._base_name("finisher_toyota") == "Toyota"
    assert tbrestore._base_name("helper_WildCard") == "WildCard"
