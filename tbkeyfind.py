"""Extract the AES-128-CBC key+iv from YOUR OWN copy of the game — no EA secret is shipped.

The key and iv are 16-char ASCII strings hardcoded in libTetrisBlitzApp.so. This finds them by
oracle validation: enumerate every 16-byte printable-ASCII window in the .so, then test each as
a key against one of your encrypted coefficient files — the right key decrypts blocks 2+ (which
are IV-independent in CBC) to printable JSON; the right iv then makes the whole thing valid JSON.

Usage:
    python tbkeyfind.py                       # auto-locates .so + a coefficient under ../Tetris blitz
    python tbkeyfind.py --so <lib.so> --coeff <Coefficients/helper.json> --out key.json
"""
import re, json, pathlib, argparse
from Crypto.Cipher import AES

SRC = pathlib.Path("..") / "Tetris blitz"
SO = SRC / "lib" / "arm64-v8a" / "libTetrisBlitzApp.so"
COEFF_DIR = SRC / "assets" / "Assets" / "Coefficients"
# AES decrypt S-box start — presence confirms a static AES implementation in the binary.
SBOX = bytes([0x52, 0x09, 0x6a, 0xd5, 0x30, 0x36, 0xa5, 0x38])   # inverse S-box head
ENC_SBOX = bytes([0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5])  # forward S-box head

def has_aes(so_bytes):
    return ENC_SBOX in so_bytes or SBOX in so_bytes

def candidates(so_bytes, min_run=16, max_run=48):
    """Every distinct 16-byte printable-ASCII window from isolated runs (keys sit in short runs,
    not inside long JSON/paths — max_run keeps the search small)."""
    out = set()
    for m in re.finditer(rb"[\x20-\x7e]{%d,}" % min_run, so_bytes):
        s = m.group()
        if len(s) <= max_run:
            for i in range(len(s) - 15):
                out.add(s[i:i + 16])
    return out

def _printable_ratio(b):
    if not b:
        return 0.0
    ok = sum(1 for c in b if 0x09 <= c <= 0x7e)
    return ok / len(b)

def _key_ok(key, head):
    """head = first >=48 bytes of ciphertext. Blocks 1..2 are IV-independent; the right key
    decrypts them to printable JSON text."""
    pt = AES.new(key, AES.MODE_CBC, b"\x00" * 16).decrypt(head[:48])
    return _printable_ratio(pt[16:48]) > 0.95

def _valid_plaintext(pt):
    """Coefficient plaintext model = json + 0x00 + PKCS7 pad. Validate + parse."""
    if not pt:
        return False
    pad = pt[-1]
    if pad < 1 or pad > 16 or pt[-pad:] != bytes([pad]) * pad:
        return False
    body = pt[:-pad].rstrip(b"\x00")
    try:
        json.loads(body.decode("utf-8"))
        return True
    except Exception:
        return False

def find_key_iv(so_bytes, sample_ct):
    """Return (key_bytes, iv_bytes) or None. sample_ct = raw bytes of one encrypted coefficient."""
    if len(sample_ct) < 48 or len(sample_ct) % 16:
        raise ValueError("sample ciphertext must be >=48 bytes and a multiple of 16")
    cands = candidates(so_bytes)
    head = sample_ct[:48]
    for key in cands:
        if not _key_ok(key, head):
            continue
        for iv in cands:                                  # only reached for a key that fits
            if _valid_plaintext(AES.new(key, AES.MODE_CBC, iv).decrypt(sample_ct)):
                return key, iv
    return None

def _find_coeff():
    if COEFF_DIR.is_dir():
        for p in sorted(COEFF_DIR.glob("*.json")):
            if p.stat().st_size >= 48:
                return p
    return None

def extract_from_game(so_path=SO, coeff_path=None, out="key.json"):
    so_path = pathlib.Path(so_path)
    coeff_path = pathlib.Path(coeff_path) if coeff_path else _find_coeff()
    if not so_path.exists():
        raise FileNotFoundError(f"no .so at {so_path}")
    if not coeff_path or not coeff_path.exists():
        raise FileNotFoundError("no encrypted coefficient found to validate against")
    so_bytes = so_path.read_bytes()
    res = find_key_iv(so_bytes, coeff_path.read_bytes())
    if not res:
        raise RuntimeError("key/iv not found — wrong .so, or an already-decrypted coefficient?")
    key, iv = res
    doc = {"key_hex": key.hex(), "iv_hex": iv.hex(), "mode": "CBC"}   # tbcrypt.load_key format
    pathlib.Path(out).write_text(json.dumps(doc), encoding="utf-8")
    return {**doc, "out": out, "aes": has_aes(so_bytes)}

def _cli():
    ap = argparse.ArgumentParser(description="Extract the AES key/iv from your own game copy.")
    ap.add_argument("--so", default=str(SO))
    ap.add_argument("--coeff", default=None, help="an encrypted Coefficients/*.json (auto if omitted)")
    ap.add_argument("--out", default="key.json")
    a = ap.parse_args()
    r = extract_from_game(a.so, a.coeff, a.out)
    print(f"key.json written -> {r['out']}  (AES found: {r['aes']}, key/iv 16 bytes each)")

if __name__ == "__main__":
    _cli()
