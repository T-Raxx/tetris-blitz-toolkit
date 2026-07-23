import pathlib, pytest
from PIL import Image
import tbinject

pytestmark = pytest.mark.skipif(not pathlib.Path(tbinject.COMMON_PNG).exists(),
                                reason="Common0.png atlas not present")

def _red(w=54, h=54):
    return Image.new("RGBA", (w, h), (255, 0, 0, 255))

def test_base_targets_map():
    t = tbinject.base_targets()
    assert t["n"] == "Common/MinoDarkBlueSingle.png"
    assert t["Y"] == "Common/MinoYellowSingle.png"

def test_frame_rect_darkblue():
    assert tbinject.frame_rect("Common/MinoDarkBlueSingle.png") == (1816, 1426, 54, 54, False)

def test_fit_into_exact_size_keeps_aspect():
    c = tbinject.fit_into(Image.new("RGBA", (10, 20)), 54, 54)
    assert c.size == (54, 54)                                   # canvas exact
    c2 = tbinject.fit_into(Image.new("RGBA", (100, 50)), 54, 54)
    assert c2.size == (54, 54)

def test_inject_over_replaces_only_target_region():
    atlas = Image.open(tbinject.COMMON_PNG).convert("RGBA")
    x, y, w, h, _ = tbinject.frame_rect("Common/MinoDarkBlueSingle.png")
    outside_before = atlas.getpixel((10, 10))
    tbinject.inject_over(atlas, "Common/MinoDarkBlueSingle.png", _red(w, h))
    assert atlas.getpixel((x + w // 2, y + h // 2)) == (255, 0, 0, 255)   # region now red
    assert atlas.getpixel((10, 10)) == outside_before                    # elsewhere untouched

def test_stage_injections_writes_common_png(tmp_path):
    src = tmp_path / "custom.png"; _red().save(src)
    res = tbinject.stage_injections([{"base": "n", "source": str(src)}], stage_dir=str(tmp_path / "st"))
    assert res["staged"] == [tbinject.COMMON_REL]
    assert res["applied"] == ["inject:n<-custom"]
    out = tmp_path / "st" / tbinject.COMMON_REL
    assert out.exists()
    atlas = Image.open(out).convert("RGBA")
    orig = Image.open(tbinject.COMMON_PNG)
    assert atlas.size == orig.size                              # in-place, no atlas resize
    x, y, w, h, _ = tbinject.frame_rect("Common/MinoDarkBlueSingle.png")
    assert atlas.getpixel((x + w // 2, y + h // 2)) == (255, 0, 0, 255)

def test_stage_injections_empty_noop(tmp_path):
    assert tbinject.stage_injections([], stage_dir=str(tmp_path)) == {"staged": [], "applied": []}

def test_catalog_resolves_loose_sources(tmp_path):
    got = tbinject.catalog_sources(str(tmp_path))
    assert "Popcorn" in got and got["Popcorn"].endswith(".png")
    assert "Bulldozer" in got
    assert all(pathlib.Path(p).exists() for p in got.values())
