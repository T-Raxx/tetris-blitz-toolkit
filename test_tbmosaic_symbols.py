import tbmosaic, tbassets

def test_symbols_colors_all_seven():
    cols = tbmosaic.symbols("colors")
    assert set(cols) == set("YRLNBnm")                 # the 7 TetriminoColor chars
    assert cols["Y"]["name"] == "Yellow"

def test_symbols_tags_powerups_and_specials():
    tags = tbmosaic.symbols("tags")
    for ch in "456789ABC":
        assert ch in tags
    assert "p" in tags and "s" in tags
    assert tags["4"]["frame"] == "Common/helper_bomb.png"

def test_symbols_groups_empty_free_brush():
    assert tbmosaic.symbols("groups") == {}

def test_tag_sprite_map_resolves_powerup_icons(tmp_path):
    got = tbassets.tag_sprite_map(str(tmp_path))
    assert "4" in got and got["4"].endswith(".png")   # bomb tag icon extracted
