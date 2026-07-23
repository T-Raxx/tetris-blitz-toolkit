import pathlib, tbnative

IB = 0x100000

def test_existing_and_swap_patches_load():
    ids = {p["id"] for p in tbnative.load_patches()}
    assert {"powerup_pace_fixed", "fps_cap", "powerup_cap_removed"} <= ids   # originals intact
    assert {"mino_gold_from_darkblue", "mino_white_from_lightblue"} <= ids   # new swaps

def test_gold_swap_rewrites_string(tmp_path):
    patches = tbnative.load_patches()
    p = next(x for x in patches if x["id"] == "mino_gold_from_darkblue")
    ga = int(p["writes"][0]["ghidra_addr"], 16); off = ga - IB
    src = pathlib.Path(tbnative.SRC_SO).read_bytes()
    assert src[off:off + 29] == b"Common/MinoDarkBlueSingle.png"       # orig present

    tbnative.stage_native(["mino_gold_from_darkblue"], patches, stage_dir=str(tmp_path))
    out = (tmp_path / "lib" / "arm64-v8a" / "libTetrisBlitzApp.so").read_bytes()
    assert out[off:off + 29].split(b"\x00")[0] == b"Common/MinoCubeYellow.png"   # swapped, null-padded
    assert len(out) == len(src)                                        # in-place, no shift

def test_swap_orig_mismatch_raises(tmp_path):
    patches = tbnative.load_patches()
    bad = dict(next(x for x in patches if x["id"] == "mino_gold_from_darkblue"))
    bad = {**bad, "id": "bad", "writes": [{**bad["writes"][0], "orig": "deadbeef"}]}
    try:
        tbnative.apply_patches(["bad"], [bad], out_so=str(tmp_path / "x.so"))
        assert False, "expected orig-mismatch ValueError"
    except ValueError as e:
        assert "orig-bytes mismatch" in str(e)
