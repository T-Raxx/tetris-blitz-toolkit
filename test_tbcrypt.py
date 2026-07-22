import json, pathlib
import tbcrypt

COEFF = pathlib.Path("..") / "Tetris blitz" / "assets" / "Assets" / "Coefficients"
KEY = tbcrypt.load_key("key.json")

def test_roundtrip_byte_identical():
    """GATE: raw decrypt then raw encrypt reproduces original ciphertext."""
    orig = (COEFF / "GameplayCoefficients.json").read_bytes()
    assert tbcrypt.encrypt_raw(tbcrypt.decrypt_raw(orig, KEY), KEY) == orig

def test_decrypt_is_valid_json():
    orig = (COEFF / "GameplayCoefficients.json").read_bytes()
    assert json.loads(tbcrypt.decrypt_json(orig, KEY))["Version"] == "41000"

def test_json_roundtrip_all_files_byte_identical():
    """decrypt_json -> encrypt_json reproduces every coefficient file byte-for-byte."""
    n = 0
    for p in COEFF.glob("*.json"):
        d = p.read_bytes()
        if len(d) % 16 or len(d) < 16:
            continue
        text = tbcrypt.decrypt_json(d, KEY)
        json.loads(text)                       # must parse
        assert tbcrypt.encrypt_json(text, KEY) == d, p.name
        n += 1
    assert n >= 50
