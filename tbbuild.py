import subprocess, zipfile, pathlib, shutil, urllib.request

SRC = pathlib.Path("..") / "Tetris blitz"
PKG = "com.ea.tetrisblitz_row"
JDK = pathlib.Path(r"C:\Program Files\Java\jdk-26.0.1\bin")
JARSIGNER = str(JDK / "jarsigner.exe")
KEYTOOL = str(JDK / "keytool.exe")
UBER_URL = "https://github.com/patrickfav/uber-apk-signer/releases/download/v1.3.0/uber-apk-signer-1.3.0.jar"

def _stored(rel):
    return rel == "resources.arsc" or rel.startswith("lib/")

def _run(args):
    p = subprocess.run(["adb", *args], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr

def ensure_keystore(path="build/debug.keystore"):
    p = pathlib.Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        subprocess.run([KEYTOOL, "-genkeypair", "-keystore", str(p), "-alias", "tb",
            "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
            "-storepass", "android", "-keypass", "android", "-dname", "CN=tb"],
            check=True, capture_output=True)
    return str(p)

def build_apk(stage_dir="mod_stage", out_apk="build/tb-modded-unsigned.apk", src=SRC):
    src = pathlib.Path(src); stage = pathlib.Path(stage_dir)
    out = pathlib.Path(out_apk); out.parent.mkdir(parents=True, exist_ok=True)
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
            z.writestr(zi, data)
    return str(out)

def _uber_sign(apk):
    jar = pathlib.Path("build/uber-apk-signer.jar")
    if not jar.exists():
        jar.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(UBER_URL, jar)
    subprocess.run(["java", "-jar", str(jar), "--apks", str(apk), "--overwrite", "--allowResign"],
                   check=True, capture_output=True)

def sign_apk(apk, keystore, out_apk="build/tb-modded.apk"):
    out = pathlib.Path(out_apk); out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(apk, out)
    r = subprocess.run([JARSIGNER, "-keystore", keystore, "-storepass", "android",
        "-sigalg", "SHA256withRSA", "-digestalg", "SHA-256", str(out), "tb"],
        capture_output=True, text=True)
    v = subprocess.run([JARSIGNER, "-verify", str(out)], capture_output=True, text=True)
    if r.returncode != 0 or "jar verified" not in v.stdout.lower():
        _uber_sign(out)
    return str(out)

def install_apk(apk, device, run=_run):
    run(["-s", device, "uninstall", PKG])
    rc, out = run(["-s", device, "install", "-r", str(apk)])
    return ("Success" in out, out)

def build_sign_install(stage_dir="mod_stage", device=None):
    import tbadb
    device = device or tbadb.device()
    if not device:
        return {"apk": None, "installed": False, "log": "no adb device found"}
    ks = ensure_keystore()
    unsigned = build_apk(stage_dir)
    signed = sign_apk(unsigned, ks)
    ok, log = install_apk(signed, device)
    return {"apk": signed, "installed": ok, "log": log, "device": device}
