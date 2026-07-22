import json, pathlib, pytest
import tbfiles, tbcrypt

COEFF = pathlib.Path("..") / "Tetris blitz" / "assets" / "Assets" / "Coefficients"
KEY = tbcrypt.load_key("key.json")
SAVE = pathlib.Path("save_PlayerData.bin")   # pulled live save (present in tbcheat)

def test_coeff_detected_and_roundtrips():
    d = (COEFF / "GameplayCoefficients.json").read_bytes()
    tb = tbfiles.load_bytes(d, KEY)
    assert tb.fmt == "coeff"
    assert tb.obj["Version"] == "41000"
    assert tbfiles.dump_bytes(tb) == d          # unedited -> byte-identical

def test_all_coeffs_roundtrip_byte_identical():
    n = 0
    for p in COEFF.glob("*.json"):
        d = p.read_bytes()
        if len(d) % 16 or len(d) < 16: continue
        tb = tbfiles.load_bytes(d, KEY)
        assert tbfiles.dump_bytes(tb) == d, p.name
        n += 1
    assert n >= 50

@pytest.mark.skipif(not SAVE.exists(), reason="live save not pulled")
def test_save_detected_and_roundtrips():
    d = SAVE.read_bytes()
    tb = tbfiles.load_bytes(d, KEY)
    assert tb.fmt == "save"
    assert tb.trailer and tb.trailer[:1] == b"\x00"
    assert "Coins" in tb.obj
    assert tbfiles.dump_bytes(tb) == d          # unedited -> byte-identical

def test_edited_coeff_reencrypts_and_reparses():
    d = (COEFF / "GameplayCoefficients.json").read_bytes()
    tb = tbfiles.load_bytes(d, KEY)
    tb.obj["NumberOfCoinsForFacebookLogin"] = 999999
    out = tbfiles.dump_bytes(tb)
    assert out != d
    tb2 = tbfiles.load_bytes(out, KEY)
    assert tb2.obj["NumberOfCoinsForFacebookLogin"] == 999999

@pytest.mark.skipif(not SAVE.exists(), reason="live save not pulled")
def test_edited_save_keeps_trailer():
    tb = tbfiles.load_bytes(SAVE.read_bytes(), KEY)
    tr = tb.trailer
    tb.obj["Coins"] = 999999999
    out = tbfiles.dump_bytes(tb)
    tb2 = tbfiles.load_bytes(out, KEY)
    assert tb2.obj["Coins"] == 999999999
    # meaningful trailer preserved immediately after JSON; compact re-serialization
    # changes total length so alignment zero-padding may follow (game ignores it;
    # confirmed safe by in-game verification per the plan).
    assert tb2.trailer.startswith(tr)
