import pathlib, tbnative

def test_assemble_write_asm_template():
    w = {"ghidra_addr": "0x00f44cb8", "orig": "c25e40b9", "asm": "mov w2, #{pace}"}
    assert tbnative.assemble_write(w, {"pace": 3}).hex() == "62008052"
    assert tbnative.assemble_write(w, {"pace": 1}).hex() == "22008052"

def test_assemble_write_plain_patch():
    w = {"ghidra_addr": "0x250000", "orig": "11223344", "patch": "aabbccdd"}
    assert tbnative.assemble_write(w, {}).hex() == "aabbccdd"

def _pace_patch(so):
    def orig(a): off = int(a, 16) - 0x100000; return so[off:off + 4].hex()
    return {"id": "pp", "name": "t", "type": "inline", "status": "ready",
            "writes": [
                {"ghidra_addr": "0x00f44cb8", "orig": orig("0x00f44cb8"), "asm": "mov w2, #{pace}"},
                {"ghidra_addr": "0x00f4f9b0", "orig": orig("0x00f4f9b0"), "asm": "mov w2, #{pace}"}]}

def test_apply_patches_asm_values(tmp_path):
    src = str(tbnative.SRC_SO); so = pathlib.Path(src).read_bytes()
    out = tbnative.apply_patches(["pp"], [_pace_patch(so)], src_so=src,
                                 out_so=str(tmp_path / "o.so"), values={"pp": {"pace": 2}})
    b = pathlib.Path(out).read_bytes()
    assert b[0xf44cb8 - 0x100000:0xf44cb8 - 0x100000 + 4].hex() == "42008052"
    assert b[0xf4f9b0 - 0x100000:0xf4f9b0 - 0x100000 + 4].hex() == "42008052"
