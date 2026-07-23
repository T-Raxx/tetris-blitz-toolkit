import pathlib, tbatlas

DB = pathlib.Path("..") / "Tetris blitz" / "assets" / "Assets" / "imagesSize150_GamePowerupsFlonase.db"

def test_parse_frames_flonase():
    frames = tbatlas.parse_frames(DB.read_bytes())
    # the real Flonase atlas: bottle + 6 particle vfx
    assert "flonase_bottle_idle" in frames
    assert all(f"flonase_pu_vfx{i}" in frames for i in range(1, 7))
    x, y, w, h = frames["flonase_pu_vfx1"]
    assert (w, h) == (87, 101)          # verified crop size
    assert 0 <= x < 1024 and 0 <= y < 512

def test_list_db_banks_finds_flonase():
    banks = tbatlas.list_db_banks()
    names = [b.name for b in banks]
    assert any("GamePowerupsFlonase.db" in n for n in names)
    assert len(banks) >= 20

def test_extract_db_writes_nonempty(tmp_path):
    rename = {f"flonase_pu_vfx{i}": f"flonase_PU_vfx{i}" for i in range(1, 7)}
    out = tbatlas.extract_db(str(DB), str(tmp_path), rename=rename)
    assert "flonase_PU_vfx1" in out            # renamed to the capital-PU name the plists expect
    from PIL import Image
    im = Image.open(out["flonase_PU_vfx1"])
    assert im.size == (87, 101) and im.getbbox() is not None
