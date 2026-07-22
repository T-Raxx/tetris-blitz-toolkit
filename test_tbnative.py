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
