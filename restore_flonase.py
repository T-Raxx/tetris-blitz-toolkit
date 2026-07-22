import json, pathlib, tbfiles, tbcrypt, tbbuild

KEY = tbcrypt.load_key("key.json")
COEFF = pathlib.Path("..") / "Tetris blitz" / "assets" / "Assets" / "Coefficients" / "helper.json"

def main():
    tb = tbfiles.load_path(str(COEFF), KEY)
    n = 0
    for h in tb.obj["helpers"]:
        if h.get("uId") == 45 or (h.get("iconBasePath") == "helper_flonase"):
            h["active"] = 1; h["unlockedByDefault"] = True; h["promotion"] = False; n += 1
    print(f"flonase entries flipped: {n}")
    stage = pathlib.Path("mod_stage") / "assets" / "Assets" / "Coefficients"
    stage.mkdir(parents=True, exist_ok=True)
    (stage / "helper.json").write_bytes(tbfiles.dump_bytes(tb))
    print("staged modded helper.json; building…")
    res = tbbuild.build_sign_install("mod_stage")
    print("device:", res.get("device"))
    print("installed:", res["installed"])
    print(res["log"][-600:])

if __name__ == "__main__":
    main()
