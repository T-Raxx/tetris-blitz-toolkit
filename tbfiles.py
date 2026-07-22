import json, copy
import tbcrypt
from Crypto.Util.Padding import pad, unpad

class TBFile:
    def __init__(self, fmt, obj, trailer, orig_plaintext, key):
        self.fmt = fmt                 # "coeff" | "save"
        self.obj = obj                 # editable dict
        self.trailer = trailer         # bytes for save, None for coeff
        self._orig_obj = copy.deepcopy(obj)
        self._orig_plaintext = orig_plaintext
        self._key = key

    @property
    def edited(self):
        return self.obj != self._orig_obj

def load_bytes(data, key=None):
    key = key or tbcrypt.load_key()
    pt = tbcrypt.decrypt_raw(data, key)
    try:
        body = unpad(pt, 16)           # valid PKCS7 => coefficient format
        fmt, trailer = "coeff", None
        json_bytes = body[:-1] if body.endswith(b"\x00") else body
    except ValueError:                 # save format: json + binary trailer
        fmt = "save"
        _, end = json.JSONDecoder().raw_decode(pt.decode("utf-8", "replace"))
        json_bytes, trailer = pt[:end], pt[end:]
    obj = json.loads(json_bytes.decode("utf-8"))
    return TBFile(fmt, obj, trailer, pt, key)

def dump_bytes(tb):
    if not tb.edited:
        return tbcrypt.encrypt_raw(tb._orig_plaintext, tb._key)   # byte-identical
    j = json.dumps(tb.obj, separators=(",", ":")).encode("utf-8")
    if tb.fmt == "coeff":
        pt = pad(j + b"\x00", 16)
    else:
        pt = j + tb.trailer
        if len(pt) % 16:
            pt += b"\x00" * (16 - len(pt) % 16)     # zero-align; needs in-game verify
    return tbcrypt.encrypt_raw(pt, tb._key)

def load_path(path, key=None):
    return load_bytes(open(path, "rb").read(), key)

def dump_path(tb, path):
    open(path, "wb").write(dump_bytes(tb))
