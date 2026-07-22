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

def apply_cave_patch(patch, src_so=SRC_SO, out_so=None):
    """Inject an R+X segment (LIEF) with a keystone-assembled guard stub and redirect the
    function entry to it. LIEF add() shifts .text by a page; we recompute the redirect vaddr
    from the .text delta and verify the original bytes there before patching."""
    import lief
    from keystone import Ks, KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN
    ks = Ks(KS_ARCH_ARM64, KS_MODE_LITTLE_ENDIAN)
    def asm(code, addr):
        enc, _ = ks.asm(code, addr=addr)
        return bytes(enc)

    red0 = int(patch["redirect"]["ghidra_addr"], 16) - IMAGE_BASE
    orig = bytes.fromhex(patch["redirect"]["orig"])
    b = lief.parse(str(src_so))
    old_text = b.get_section(".text").virtual_address
    if bytes(b.get_content_from_virtual_address(red0, len(orig))) != orig:
        raise ValueError(f"redirect orig mismatch for {patch['id']} (pre-add)")

    seg = lief.ELF.Segment()
    seg.type = lief.ELF.Segment.TYPE.LOAD
    seg.flags = lief.ELF.Segment.FLAGS.R | lief.ELF.Segment.FLAGS.X
    seg.content = [0] * 0x40
    added = b.add(seg)
    V = added.virtual_address
    shift = b.get_section(".text").virtual_address - old_text
    red = red0 + shift
    if bytes(b.get_content_from_virtual_address(red, len(orig))) != orig:
        raise ValueError(f"redirect orig mismatch for {patch['id']} (post-add shift={hex(shift)})")

    back = red + len(orig)
    guard0 = asm(patch["guard_asm"].format(skip="#0"), V)
    disp0 = asm(patch["displaced_asm"], V + len(guard0))
    skip_va = V + len(guard0) + len(disp0) + 4          # +4 for the b-back
    guard = asm(patch["guard_asm"].format(skip=hex(skip_va)), V)
    disp = asm(patch["displaced_asm"], V + len(guard))
    b_back = asm("b #" + hex(back), V + len(guard) + len(disp))
    ret = asm("ret", skip_va)
    stub = guard + disp + b_back + ret
    stub = stub + b"\x00" * (0x40 - len(stub))
    added.content = list(stub)
    b.patch_address(red, list(asm("b #" + hex(V), red)))

    out = pathlib.Path(out_so) if out_so else pathlib.Path("build") / "libTetrisBlitzApp.patched.so"
    out.parent.mkdir(parents=True, exist_ok=True)
    b.write(str(out))
    return str(out)

def apply_patches(patch_ids, patches, src_so=SRC_SO, out_so=None):
    byid = {p["id"]: p for p in patches}
    inline = [byid[i] for i in patch_ids if byid[i].get("type", "inline") == "inline"]
    caves = [byid[i] for i in patch_ids if byid[i].get("type") == "cave"]
    out = pathlib.Path(out_so) if out_so else pathlib.Path("build") / "libTetrisBlitzApp.patched.so"
    out.parent.mkdir(parents=True, exist_ok=True)

    data = bytearray(pathlib.Path(src_so).read_bytes())
    for p in inline:
        if not verify(data, p):
            raise ValueError(f"orig-bytes mismatch for patch {p['id']}")
        for w in p.get("writes", []):
            off = _off(w["ghidra_addr"]); pb = bytes.fromhex(w["patch"])
            data[off:off + len(pb)] = pb
    if not caves:
        out.write_bytes(bytes(data))
        return str(out)

    tmp = pathlib.Path("build") / "_stage_inline.so"; tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_bytes(bytes(data)); cur = str(tmp)
    for i, p in enumerate(caves):
        dst = str(out) if i == len(caves) - 1 else str(pathlib.Path("build") / f"_cave{i}.so")
        apply_cave_patch(p, src_so=cur, out_so=dst); cur = dst
    return str(out)

def stage_native(patch_ids, patches, stage_dir="mod_stage"):
    dest = pathlib.Path(stage_dir) / "lib" / "arm64-v8a" / "libTetrisBlitzApp.so"
    dest.parent.mkdir(parents=True, exist_ok=True)
    apply_patches(patch_ids, patches, out_so=str(dest))
    return {"staged": [SO_REL], "applied": list(patch_ids)}
