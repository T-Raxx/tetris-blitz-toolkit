import pathlib, json
import tbnative

def _fake_so(tmp):
    data = bytearray(b"\x00" * 0x200000)
    data[0x150000:0x150004] = b"\x11\x22\x33\x44"
    p = tmp / "lib.so"; p.write_bytes(data); return p

def _patch(ghidra_addr="0x250000", orig="11223344", patch="aabbccdd"):
    return {"id": "p1", "name": "t", "status": "wip", "note": "",
            "writes": [{"ghidra_addr": ghidra_addr, "orig": orig, "patch": patch}]}

def test_verify_true_and_false(tmp_path):
    so = _fake_so(tmp_path).read_bytes()
    assert tbnative.verify(so, _patch()) is True
    assert tbnative.verify(so, _patch(orig="deadbeef")) is False

def test_apply_patches_changes_only_offset(tmp_path):
    src = _fake_so(tmp_path)
    out = tbnative.apply_patches(["p1"], [_patch()], src_so=str(src), out_so=str(tmp_path / "o.so"))
    a = bytearray(src.read_bytes()); b = pathlib.Path(out).read_bytes()
    assert b[0x150000:0x150004] == bytes.fromhex("aabbccdd")
    a[0x150000:0x150004] = bytes.fromhex("aabbccdd")
    assert bytes(a) == b

def test_apply_rejects_mismatch(tmp_path):
    src = _fake_so(tmp_path)
    try:
        tbnative.apply_patches(["p1"], [_patch(orig="deadbeef")], src_so=str(src), out_so=str(tmp_path / "o.so"))
        assert False, "should have raised"
    except ValueError:
        pass

def test_stage_native_writes_lib(tmp_path):
    src = _fake_so(tmp_path)
    dest = tmp_path / "stage" / "lib" / "arm64-v8a" / "libTetrisBlitzApp.so"
    tbnative.apply_patches(["p1"], [_patch()], src_so=str(src), out_so=str(dest))
    assert dest.exists() and pathlib.Path(dest).read_bytes()[0x150000:0x150004] == bytes.fromhex("aabbccdd")

def test_load_patches_reads_registry():
    ps = tbnative.load_patches("native_patches.json")
    assert isinstance(ps, list)

def _flonase_like_patch(so_bytes):
    off = 0xb8bf0c - 0x100000
    return {"id": "cave1", "name": "t", "type": "cave", "status": "wip", "note": "",
            "redirect": {"ghidra_addr": "0x00b8bf0c", "orig": so_bytes[off:off + 4].hex()},
            "displaced_asm": "stp d9, d8, [sp, #-0x70]!",
            "guard_asm": "cmp x0, #0x1000\nb.lo {skip}"}

def test_apply_cave_patch_injects_and_redirects(tmp_path):
    import lief
    src = str(tbnative.SRC_SO)
    so = open(src, "rb").read()
    out = tbnative.apply_cave_patch(_flonase_like_patch(so), src_so=src, out_so=str(tmp_path / "c.so"))
    b0 = lief.parse(src); b1 = lief.parse(out)
    assert len(b1.segments) == len(b0.segments) + 1
    # LIEF add() shifts .text; the redirect lives at the shifted vaddr and is now a B
    shift = b1.get_section(".text").virtual_address - b0.get_section(".text").virtual_address
    red = (0xb8bf0c - 0x100000) + shift
    br = bytes(b1.get_content_from_virtual_address(red, 4))
    assert (int.from_bytes(br, "little") >> 26) == 0b000101

def test_apply_cave_rejects_mismatch(tmp_path):
    src = str(tbnative.SRC_SO); so = open(src, "rb").read()
    p = _flonase_like_patch(so); p["redirect"]["orig"] = "deadbeef"
    try:
        tbnative.apply_cave_patch(p, src_so=src, out_so=str(tmp_path / "c.so"))
        assert False
    except ValueError:
        pass

def test_stage_native_cave(tmp_path):
    import lief
    src = str(tbnative.SRC_SO); so = open(src, "rb").read()
    p = _flonase_like_patch(so)
    out = tbnative.apply_patches(["cave1"], [p], src_so=src, out_so=str(tmp_path / "o.so"))
    assert len(lief.parse(out).segments) == len(lief.parse(src).segments) + 1
