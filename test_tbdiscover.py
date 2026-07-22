import json, pathlib
import tbdiscover

def test_disabled_includes_flonase():
    d = tbdiscover.detect_disabled_powerups()
    assert any(f["meta"].get("uId") == 45 for f in d)          # Flonase
    assert all(f["category"] == "disabled_powerup" for f in d)

def test_orphans_include_antigravity_test():
    idx = tbdiscover.atlas_index(); refs = tbdiscover.reference_tokens()
    orphans = tbdiscover.detect_orphan_sprites(idx, refs)
    ids = {f["title"] for f in orphans}
    assert "AntiGravity_Test" in ids
    assert len(orphans) > 100

def test_event_branded_finds_flonase_or_july():
    idx = tbdiscover.atlas_index()
    ev = tbdiscover.detect_event_branded(idx)
    pats = {f["meta"].get("pattern") for f in ev}
    assert "flonase" in pats or "july" in pats

def test_build_catalog(tmp_path):
    cat = tbdiscover.build_catalog(str(tmp_path / "cache"))
    assert cat["counts"].get("disabled_powerup", 0) > 5
    assert sum(cat["counts"].values()) > 100
    assert (tmp_path / "cache" / "catalog.json").exists()
    assert any(f.get("thumbs") for f in cat["findings"])
    orphan_titles = {f["title"] for f in cat["findings"] if f["category"] == "orphan_sprite"}
    assert "helper_flonase" not in orphan_titles
