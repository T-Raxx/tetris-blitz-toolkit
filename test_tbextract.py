import pathlib, tbextract

def test_enumerate_sources_has_all_types():
    srcs = tbextract.enumerate_sources()
    types = {s["type"] for s in srcs}
    assert {"db", "atlas"} <= types            # loose may be empty on some trees
    assert any(s["type"] == "db" and "Flonase" in s["path"] for s in srcs)

def test_extract_all_dumps_db_frames(tmp_path):
    res = tbextract.extract_all(str(tmp_path))
    assert res["count"] > 0 and res["by_type"]["db"] > 0
    hits = list(pathlib.Path(tmp_path).glob("db/*/flonase_bottle_idle.png"))
    assert hits, "flonase_bottle_idle not extracted"
