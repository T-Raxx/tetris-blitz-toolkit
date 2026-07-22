import tbsemantics as S

def test_curated_override_wins():
    d = S.describe("totalNumRows", "helper_frostbite")
    assert d["label"] == "Rows to freeze"

def test_autoderive_camel_and_ms():
    d = S.describe("minoAnimationTimeMs")
    assert d["label"] == "Mino Animation Time (ms)"
    assert d["tooltip"] == "minoAnimationTimeMs"

def test_autoderive_byte_prefix_hint_and_colour():
    d = S.describe("BYTE_bonusScoreTextInnerColourR")
    assert d["hint"] == "byte(0-255)"
    assert "R" in d["label"] and "Byte" not in d["label"]

def test_autoderive_never_blank():
    assert S.describe("x")["label"].strip()

def test_core_cheats_has_gametime():
    keys = [c["key"] for c in S.CORE_CHEATS]
    assert "GameTimeInMs" in keys
    assert all(c.get("label") for c in S.CORE_CHEATS)
