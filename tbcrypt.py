"""Tetris Blitz coefficient/save crypto tool.

AES-128-CBC, fixed key+iv (from Ghidra FUN_00f04480). Plaintext model:
    plaintext = json_text + b"\\x00" + PKCS7pad(16)
"""
import json, sys
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

def load_key(path="key.json"):
    k = json.load(open(path))
    k["key"] = bytes.fromhex(k["key_hex"])
    k["iv"] = bytes.fromhex(k["iv_hex"])
    return k

def _cipher(k):
    assert k["mode"] == "CBC"
    return AES.new(k["key"], AES.MODE_CBC, k["iv"])

def decrypt_raw(data, k):
    return _cipher(k).decrypt(data)

def encrypt_raw(data, k):
    assert len(data) % 16 == 0, "raw input must be block-aligned"
    return _cipher(k).encrypt(data)

def decrypt_json(data, k):
    pt = unpad(decrypt_raw(data, k), 16)      # strip PKCS7
    if pt.endswith(b"\x00"):                  # strip C null-terminator
        pt = pt[:-1]
    return pt.decode("utf-8")

def encrypt_json(text, k):
    return encrypt_raw(pad(text.encode("utf-8") + b"\x00", 16), k)

def _main():
    op, src, dst = sys.argv[1], sys.argv[2], sys.argv[3]
    k = load_key()
    if op == "decrypt-raw":    open(dst, "wb").write(decrypt_raw(open(src, "rb").read(), k))
    elif op == "encrypt-raw":  open(dst, "wb").write(encrypt_raw(open(src, "rb").read(), k))
    elif op == "decrypt-json": open(dst, "w", encoding="utf-8").write(decrypt_json(open(src, "rb").read(), k))
    elif op == "encrypt-json": open(dst, "wb").write(encrypt_json(open(src, encoding="utf-8").read(), k))
    else: sys.exit("ops: decrypt-raw|encrypt-raw|decrypt-json|encrypt-json <in> <out>")

if __name__ == "__main__":
    _main()
