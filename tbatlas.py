"""Extract EA DBPF texture-bank .db files (imagesSize*_GamePowerups*.db) into loose PNG frames.

Format: DBPF v2.1 package with a stored atlas PNG + a QFS/RefPack-compressed (0x10FB) frame table.
Each 152-byte frame record = name[64] + atlasName[64] + {u32 w, u32 h, u32 atlasW, u32 atlasH,
f32 u=x/atlasW, f32 v=y/atlasH}. Verified against imagesSize150_GamePowerupsFlonase.db (the Flonase
nasal-spray bottle + 6 particle vfx frames crop pixel-perfect)."""
import struct, re, pathlib, io

ASSETS = pathlib.Path("..") / "Tetris blitz" / "assets" / "Assets"

def list_db_banks(assets_dir=ASSETS):
    return sorted(pathlib.Path(assets_dir).glob("imagesSize*_*.db"))

def qfs_decompress(data):
    """Decode EA QFS/RefPack starting at/after the 0x10FB signature."""
    p = data.find(b"\x10\xfb")
    if p < 0:
        raise ValueError("no QFS signature")
    i = p + 2
    outlen = (data[i] << 16) | (data[i + 1] << 8) | data[i + 2]; i += 3
    out = bytearray()
    while i < len(data) and len(out) < outlen:
        b0 = data[i]; i += 1
        if b0 < 0x80:
            b1 = data[i]; i += 1; n = b0 & 3; out += data[i:i + n]; i += n
            c = ((b0 & 0x1c) >> 2) + 3; off = ((b0 & 0x60) << 3) + b1 + 1
        elif b0 < 0xC0:
            b1 = data[i]; b2 = data[i + 1]; i += 2; n = (b1 >> 6) & 3; out += data[i:i + n]; i += n
            c = (b0 & 0x3f) + 4; off = ((b1 & 0x3f) << 8) + b2 + 1
        elif b0 < 0xE0:
            b1 = data[i]; b2 = data[i + 1]; b3 = data[i + 2]; i += 3
            n = b0 & 3; out += data[i:i + n]; i += n
            c = ((b0 & 0x0c) << 6) + b3 + 5; off = ((b0 & 0x10) << 12) + (b1 << 8) + b2 + 1
        elif b0 < 0xFC:
            n = ((b0 & 0x1f) << 2) + 4; out += data[i:i + n]; i += n; c = 0; off = 0
        else:
            n = b0 & 3; out += data[i:i + n]; i += n; c = 0; off = 0
        for _ in range(c):
            out.append(out[len(out) - off])
    return bytes(out)

def parse_frames(db_bytes):
    """Return {frame_name: (x, y, w, h)} from the QFS frame table."""
    meta = qfs_decompress(db_bytes[db_bytes.find(b"\x10\xfb", 0x80):])
    frames = {}
    for m in re.finditer(rb"/[A-Za-z0-9_]+\.tga", meta):
        s = m.start()
        name = meta[s:meta.find(b"\x00", s)].decode().lstrip("/")[:-4]  # strip leading / and .tga
        r = meta[s + 0x80:s + 0x80 + 24]
        w, h, aw, ah = struct.unpack("<IIII", r[:16]); u, v = struct.unpack("<ff", r[16:24])
        frames[name] = (round(u * aw), round(v * ah), w, h)
    return frames

def atlas_image(db_bytes):
    from PIL import Image
    ps = db_bytes.find(b"\x89PNG"); pe = db_bytes.find(b"IEND", ps) + 8
    return Image.open(io.BytesIO(db_bytes[ps:pe])).convert("RGBA")

def write_cocos_plist(frames, texture_name, atlas_wh, out_plist):
    """Write a cocos2d-x v2 SpriteFrame plist. `frames` = {frame_key: (x, y, w, h)}. The atlas texture
    (referenced by `texture_name`) must sit next to `out_plist`."""
    import plistlib
    aw, ah = atlas_wh
    fr = {}
    for key, (x, y, w, h) in frames.items():
        fr[key] = {"frame": f"{{{{{x},{y}}},{{{w},{h}}}}}", "offset": "{0,0}", "rotated": False,
                   "sourceColorRect": f"{{{{0,0}},{{{w},{h}}}}}", "sourceSize": f"{{{w},{h}}}"}
    doc = {"frames": fr, "metadata": {"format": 2, "textureFileName": texture_name,
           "realTextureFileName": texture_name, "size": f"{{{aw},{ah}}}"}}
    pathlib.Path(out_plist).write_bytes(plistlib.dumps(doc))

def extract_db(db_path, out_dir, rename=None):
    """Crop every frame in `db_path` to `out_dir/<name>.png`. `rename` maps frame_name -> out
    filename (without .png) to satisfy case/extension mismatches the code expects. Returns
    {out_name: path}."""
    d = pathlib.Path(db_path).read_bytes()
    atlas = atlas_image(d); frames = parse_frames(d)
    out = pathlib.Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    written = {}
    for name, (x, y, w, h) in frames.items():
        fn = (rename or {}).get(name, name)
        p = out / (fn + ".png")
        atlas.crop((x, y, x + w, y + h)).save(p)
        written[fn] = str(p)
    return written
