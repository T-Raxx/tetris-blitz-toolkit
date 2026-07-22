import json, pathlib

IMAGE_BASE = 0x100000
SRC_SO = pathlib.Path("..") / "Tetris blitz" / "lib" / "arm64-v8a" / "libTetrisBlitzApp.so"
SO_REL = "lib/arm64-v8a/libTetrisBlitzApp.so"

def load_patches(path="native_patches.json"):
    p = pathlib.Path(path)
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8")).get("patches", [])

def _off(ghidra_addr):
    return int(ghidra_addr, 16) - IMAGE_BASE

def verify(so_bytes, patch):
    for w in patch.get("writes", []):
        off = _off(w["ghidra_addr"]); orig = bytes.fromhex(w["orig"])
        if bytes(so_bytes[off:off + len(orig)]) != orig:
            return False
    return True

def apply_patches(patch_ids, patches, src_so=SRC_SO, out_so=None):
    data = bytearray(pathlib.Path(src_so).read_bytes())
    byid = {p["id"]: p for p in patches}
    for pid in patch_ids:
        p = byid[pid]
        if not verify(data, p):
            raise ValueError(f"orig-bytes mismatch for patch {pid}")
        for w in p.get("writes", []):
            off = _off(w["ghidra_addr"]); pb = bytes.fromhex(w["patch"])
            data[off:off + len(pb)] = pb
    out = pathlib.Path(out_so) if out_so else pathlib.Path("build") / "libTetrisBlitzApp.patched.so"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bytes(data))
    return str(out)

def stage_native(patch_ids, patches, stage_dir="mod_stage"):
    dest = pathlib.Path(stage_dir) / "lib" / "arm64-v8a" / "libTetrisBlitzApp.so"
    dest.parent.mkdir(parents=True, exist_ok=True)
    apply_patches(patch_ids, patches, out_so=str(dest))
    return {"staged": [SO_REL], "applied": list(patch_ids)}
