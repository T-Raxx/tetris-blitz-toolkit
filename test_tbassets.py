import os, pathlib, plistlib, pytest
import tbassets
from PIL import Image

ATLAS_PRESENT = os.path.exists(tbassets.ATLAS)

def _make_atlas(tmp):
    img = Image.new("RGBA", (32, 16))
    for x in range(16):
        for y in range(16):
            img.putpixel((x, y), (220, 30, 30, 255))
            img.putpixel((16 + x, y), (40, 80, 220, 255))
    apath = tmp / "atlas.png"; img.save(apath)
    frames = {
        "red.png": {"frame": "{{0,0},{16,16}}", "rotated": False},
        "blue.png": {"frame": "{{16,0},{16,16}}", "rotated": False},
    }
    ppath = tmp / "atlas.plist"
    ppath.write_bytes(plistlib.dumps({"frames": frames}))
    return ppath, apath

def test_extract_atlas_crops_frames(tmp_path):
    ppath, apath = _make_atlas(tmp_path)
    out = tbassets.extract_atlas(str(tmp_path / "cache"), plist=str(ppath), atlas=str(apath))
    assert set(k for k in out) == {"red.png", "blue.png"}
    im = Image.open(out["red.png"])
    assert im.size == (16, 16)
    assert im.convert("RGB").getpixel((8, 8)) == (220, 30, 30)

def test_dominant_and_automap(tmp_path):
    ppath, apath = _make_atlas(tmp_path)
    out = tbassets.extract_atlas(str(tmp_path / "cache"), plist=str(ppath), atlas=str(apath))
    assert tbassets.dominant_color(out["red.png"])[0] > 150
    m = tbassets.auto_map_blocks([out["red.png"], out["blue.png"]], "RB")
    assert Image.open(m["R"]).convert("RGB").getpixel((8, 8))[0] > 150
    assert Image.open(m["B"]).convert("RGB").getpixel((8, 8))[2] > 150

def _png_bytes():
    img = Image.new("RGBA", (2, 2), (10, 20, 30, 255))
    import io; b = io.BytesIO(); img.save(b, "PNG"); return b.getvalue()

def test_carve_pngs_finds_embedded(tmp_path):
    png = _png_bytes()
    blob = b"\x00\x11" * 40 + png + b"\xff" * 20
    db = tmp_path / "x.db"; db.write_bytes(blob)
    got = tbassets.carve_pngs(str(db), str(tmp_path / "carved"))
    assert len(got) == 1
    assert Image.open(got[0]).size == (2, 2)

def test_letter_color_covers_all_letters():
    for ch in "YLNBRmn":
        assert ch in tbassets.LETTER_COLOR
    assert tbassets.POWERUP_NAME["4"] == "Bombs"

@pytest.mark.skipif(not ATLAS_PRESENT, reason="game atlas not present")
def test_block_sprite_map_real(tmp_path):
    m = tbassets.block_sprite_map(str(tmp_path / "c"), "YLNBR")
    assert set(m) == set("YLNBR")
    r, g, b = tbassets.dominant_color(m["Y"])   # Y -> yellowish sprite
    assert r > 120 and g > 100 and b < 130

@pytest.mark.skipif(not ATLAS_PRESENT, reason="game atlas not present")
def test_powerup_icon_map_real(tmp_path):
    m = tbassets.powerup_icon_map(str(tmp_path / "c"))
    assert "4" in m and os.path.exists(m["4"])
