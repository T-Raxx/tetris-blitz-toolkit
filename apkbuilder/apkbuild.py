"""Standalone redistributable-APK builder for modded Tetris Blitz.

Repacks the base APK tree with mod_stage overrides and signs v1+v2+v3 via uber-apk-signer
(zipalign included), producing an APK installable on real, non-rooted hardware — Android 12+
rejects v1-only signatures (MuMu tolerated them, real phones don't).

Self-contained: NO tbcheat imports. Usable as CLI or importable build().
    python apkbuild.py --mods ../tbcheat/mod_stage --out dist/tetrisblitz-modded.apk
"""
import subprocess, zipfile, pathlib, urllib.request, hashlib, argparse

HERE = pathlib.Path(__file__).resolve().parent    # <repo>/apkbuilder
REPO = HERE.parent                                # <repo> (tbcheat)
DEFAULT_SRC = REPO.parent / "Tetris blitz"        # unpacked base APK tree (sibling of the repo)
DEFAULT_MODS = REPO / "mod_stage"
UBER_VER = "1.3.0"
UBER_URL = f"https://github.com/patrickfav/uber-apk-signer/releases/download/v{UBER_VER}/uber-apk-signer-{UBER_VER}.jar"
UBER_JAR = HERE / "tools" / f"uber-apk-signer-{UBER_VER}.jar"

def _stored(rel):
    return rel == "resources.arsc" or rel.startswith("lib/")

def repack(stage_dir, out_apk, src=DEFAULT_SRC):
    """Zip the base tree with mod_stage overrides (STORE arsc+lib, drop META-INF, add new files)."""
    src = pathlib.Path(src); stage = pathlib.Path(stage_dir)
    out = pathlib.Path(out_apk); out.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    with zipfile.ZipFile(out, "w") as z:
        for f in sorted(src.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(src).as_posix()
            if rel.startswith("META-INF/"):
                continue
            override = stage / rel
            data = override.read_bytes() if override.exists() else f.read_bytes()
            zi = zipfile.ZipInfo(rel)
            zi.compress_type = zipfile.ZIP_STORED if _stored(rel) else zipfile.ZIP_DEFLATED
            z.writestr(zi, data); seen.add(rel)
        for f in sorted(stage.rglob("*")):                     # mod_stage-only new files
            if not f.is_file():
                continue
            rel = f.relative_to(stage).as_posix()
            if rel in seen or rel.startswith("META-INF/"):
                continue
            zi = zipfile.ZipInfo(rel)
            zi.compress_type = zipfile.ZIP_STORED if _stored(rel) else zipfile.ZIP_DEFLATED
            z.writestr(zi, f.read_bytes())
    return str(out)

def ensure_uber():
    if not UBER_JAR.exists():
        UBER_JAR.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(UBER_URL, UBER_JAR)
    return str(UBER_JAR)

def sign(apk, keystore=None, run=subprocess.run):
    """v1+v2+v3 + zipalign in place via uber-apk-signer. No keystore -> uber's debug key (fine for
    sideload/testing). Returns the (overwritten) apk path."""
    jar = ensure_uber()
    args = ["java", "-jar", jar, "--apks", str(apk), "--overwrite", "--allowResign"]
    if keystore:
        args += ["--ks", str(keystore), "--ksAlias", "tb", "--ksPass", "android", "--ksKeyPass", "android"]
    run(args, check=True, capture_output=True)
    return str(apk)

def verify(apk, run=subprocess.run):
    jar = ensure_uber()
    r = run(["java", "-jar", jar, "--apks", str(apk), "--verify", "--onlyVerify"],
            capture_output=True, text=True)
    return (getattr(r, "stdout", "") or "") + (getattr(r, "stderr", "") or "")

def sha256(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def build(stage_dir=DEFAULT_MODS, out_apk="dist/tetrisblitz-modded.apk", src=DEFAULT_SRC,
          keystore=None, do_sign=True, run=subprocess.run):
    """Repack + (optionally) sign v2+. Returns {apk, sha256, signed, verify?}."""
    out = pathlib.Path(out_apk)
    if not out.is_absolute():
        out = HERE / out
    repack(stage_dir, out, src)
    res = {"apk": str(out), "signed": False}
    if do_sign:
        sign(out, keystore, run=run)
        res["signed"] = True
        res["verify"] = verify(out, run=run)
    res["sha256"] = sha256(out)
    return res

def _cli():
    ap = argparse.ArgumentParser(description="Build a redistributable, v2-signed modded Tetris Blitz APK.")
    ap.add_argument("--mods", default=str(DEFAULT_MODS), help="mod_stage dir with overrides")
    ap.add_argument("--base", default=str(DEFAULT_SRC), help="unpacked base APK tree")
    ap.add_argument("--out", default="dist/tetrisblitz-modded.apk")
    ap.add_argument("--ks", default=None, help="keystore (alias tb, pass android); default = uber debug key")
    ap.add_argument("--no-sign", action="store_true")
    a = ap.parse_args()
    r = build(a.mods, a.out, src=a.base, keystore=a.ks, do_sign=not a.no_sign)
    print("APK   :", r["apk"])
    print("sha256:", r["sha256"])
    print("signed:", r["signed"])
    if r.get("verify"):
        print(r["verify"])

if __name__ == "__main__":
    _cli()
