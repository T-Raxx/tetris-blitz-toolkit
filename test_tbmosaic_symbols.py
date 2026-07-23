import tbmosaic, tbassets

def test_symbols_colors_twelve_chars():
    cols = tbmosaic.symbols("colors")
    assert set(cols) == set("YRLGBNWmnorw")            # every color char across the 6 finishers
    assert cols["Y"]["name"] == "Yellow" and cols["Y"]["conf"] == "confirmed"
    assert cols["G"]["conf"] == "confirmed" and cols["R"]["conf"] == "confirmed"
    assert cols["W"]["conf"] == "special"             # GiftTree brown trunk, no generic enum

def test_symbols_tags_powerups_and_progressive():
    tags = tbmosaic.symbols("tags")
    for ch in "123456789ABC":              # the tag chars actually used in shipped finisher grids
        assert ch in tags and tags[ch].get("frame")
    assert "p" in tags and "s" in tags     # Progressive background minos (not placeable powerups)
    assert tags["1"]["name"] == "Quake"

def test_finisher_palettes_match_shipped_grids():
    assert tbmosaic.finisher_palette("SuperNova") == list("BLNRY")
    assert tbmosaic.finisher_palette("GiftTree") == list("GWY")
    assert tbmosaic.finisher_name("decrypted/GiftTree.json") == "GiftTree"
    assert tbmosaic.finisher_name("Coefficients/SuperNova.json") == "SuperNova"
    assert tbmosaic.finisher_name("random.json") is None

def test_symbols_groups_empty_free_brush():
    assert tbmosaic.symbols("groups") == {}

def test_tag_sprite_map_resolves_powerup_icons(tmp_path):
    got = tbassets.tag_sprite_map(str(tmp_path))
    assert "4" in got and got["4"].endswith(".png")   # bomb tag icon extracted

def test_color_frame_map_confident_only(tmp_path):
    fm = tbassets.color_frame_map()
    assert fm["Y"] == "Common/MinoYellowSingle.png"
    assert "W" not in fm and "o" not in fm            # no confident frame -> swatch fallback
    got = tbassets.block_sprite_map(str(tmp_path))
    assert "Y" in got and got["Y"].endswith(".png") and "W" not in got
