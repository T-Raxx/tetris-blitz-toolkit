import pathlib, tbdiscover

def test_detect_db_assets(tmp_path):
    finds = tbdiscover.detect_db_assets(str(tmp_path))
    assert finds and all(f["category"] == "db_asset" for f in finds)
    bottle = [f for f in finds if f["title"] == "flonase_bottle_idle"]
    assert bottle and pathlib.Path(bottle[0]["thumbs"][0]).exists()

def test_build_catalog_includes_db(tmp_path):
    cat = tbdiscover.build_catalog(str(tmp_path), include_db=True)
    assert cat["counts"].get("db_asset", 0) > 0

def test_build_catalog_includes_sounds(tmp_path):
    cat = tbdiscover.build_catalog(str(tmp_path), include_db=False, include_sounds=True)
    assert cat["counts"].get("sound", 0) > 200
