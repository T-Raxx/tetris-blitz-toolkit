import json, pathlib
import tbgallery

def _fake_cache(tmp_path):
    cache = tmp_path / "cache"; (cache / "thumbnails").mkdir(parents=True)
    from PIL import Image
    p = cache / "thumbnails" / "helper_flonase.png"
    Image.new("RGBA", (8, 8), (0, 200, 0, 255)).save(p)
    catalog = {"counts": {"disabled_powerup": 1, "orphan_sprite": 1},
        "findings": [
            {"category": "disabled_powerup", "id": "helper_45", "title": "Flonase",
             "status": "active=2 promo", "source_file": "helper.json", "sprites": ["helper_flonase"],
             "meta": {}, "thumbs": [str(p)]},
            {"category": "orphan_sprite", "id": "sprite_AntiGravity_Test", "title": "AntiGravity_Test",
             "status": "orphan candidate", "source_file": "Scene_Game0.plist", "sprites": ["AntiGravity_Test"],
             "meta": {}, "thumbs": []}]}
    (cache / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
    return cache

def test_render_html_self_contained(tmp_path):
    cache = _fake_cache(tmp_path)
    out = tbgallery.render_html(str(cache), str(tmp_path / "g.html"))
    doc = pathlib.Path(out).read_text(encoding="utf-8")
    assert "Flonase" in doc and "AntiGravity_Test" in doc
    assert "disabled_powerup" in doc and "orphan_sprite" in doc
    assert "data:image/png;base64," in doc
    assert 'src="http' not in doc and 'href="http' not in doc
