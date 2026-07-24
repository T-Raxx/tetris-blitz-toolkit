import json, pathlib, pytest
import tbkeyfind, tbcrypt

_SO = tbkeyfind.SO
_COEFF = tbkeyfind._find_coeff()
pytestmark = pytest.mark.skipif(not (_SO.exists() and _COEFF and _COEFF.exists()),
                                reason="game .so / coefficients not present (user-supplied)")

def test_candidates_and_aes_detected():
    sob = _SO.read_bytes()
    assert tbkeyfind.has_aes(sob)                          # static AES present
    assert len(tbkeyfind.candidates(sob)) > 100            # plenty of 16-char windows

def test_find_key_iv_decrypts_a_coefficient():
    sob = _SO.read_bytes()
    res = tbkeyfind.find_key_iv(sob, _COEFF.read_bytes())
    assert res is not None
    key, iv = res
    assert len(key) == 16 and len(iv) == 16
    # the recovered key/iv must actually decrypt a coefficient to valid JSON
    k = {"key": key, "iv": iv, "mode": "CBC"}
    txt = tbcrypt.decrypt_json(_COEFF.read_bytes(), k)
    assert json.loads(txt)                                 # round-trips to real JSON

def test_extract_writes_tbcrypt_format(tmp_path):
    out = tmp_path / "key.json"
    r = tbkeyfind.extract_from_game(str(_SO), str(_COEFF), str(out))
    doc = json.loads(out.read_text())
    assert set(doc) == {"key_hex", "iv_hex", "mode"} and doc["mode"] == "CBC"
    assert len(bytes.fromhex(doc["key_hex"])) == 16 and len(bytes.fromhex(doc["iv_hex"])) == 16
    # the written key.json must load + decrypt via tbcrypt
    k = tbcrypt.load_key(str(out))
    assert json.loads(tbcrypt.decrypt_json(_COEFF.read_bytes(), k))

def test_recovered_matches_existing_keyjson_if_present():
    if not pathlib.Path("key.json").exists():
        pytest.skip("no local key.json to compare against")
    known = json.load(open("key.json"))
    res = tbkeyfind.find_key_iv(_SO.read_bytes(), _COEFF.read_bytes())
    key, iv = res
    assert key.hex() == known["key_hex"] and iv.hex() == known["iv_hex"]
