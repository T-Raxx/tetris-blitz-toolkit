import os, zipfile, pathlib, shutil, pytest
import tbbuild

JDK_OK = pathlib.Path(tbbuild.JARSIGNER).exists()

def _synthetic_src(tmp):
    src = tmp / "src"; (src / "lib" / "arm64-v8a").mkdir(parents=True)
    (src / "assets" / "Assets" / "Coefficients").mkdir(parents=True)
    (src / "META-INF").mkdir()
    (src / "resources.arsc").write_bytes(b"ARSC" * 100)
    (src / "lib" / "arm64-v8a" / "libx.so").write_bytes(b"\x7fELF" + b"\x00" * 500)
    (src / "assets" / "Assets" / "Coefficients" / "helper.json").write_bytes(b"ORIGINAL")
    (src / "META-INF" / "CERT.RSA").write_bytes(b"oldsig")
    (src / "AndroidManifest.xml").write_bytes(b"\x03\x00")
    return src

def test_build_apk_swaps_and_stores(tmp_path):
    src = _synthetic_src(tmp_path)
    stage = tmp_path / "stage" / "assets" / "Assets" / "Coefficients"
    stage.mkdir(parents=True)
    (stage / "helper.json").write_bytes(b"MODDED")
    out = tbbuild.build_apk(str(tmp_path / "stage"), str(tmp_path / "o.apk"), src=src)
    z = zipfile.ZipFile(out)
    names = z.namelist()
    assert "assets/Assets/Coefficients/helper.json" in names
    assert z.read("assets/Assets/Coefficients/helper.json") == b"MODDED"
    assert not any(n.startswith("META-INF/") for n in names)
    assert z.getinfo("resources.arsc").compress_type == zipfile.ZIP_STORED
    assert z.getinfo("lib/arm64-v8a/libx.so").compress_type == zipfile.ZIP_STORED
    assert z.getinfo("AndroidManifest.xml").compress_type == zipfile.ZIP_DEFLATED

def test_install_apk_uninstalls_first():
    order = []
    def run(args):
        order.append(args)
        return (0, "Success\n") if ("install" in args and "uninstall" not in args) else (0, "")
    ok, out = tbbuild.install_apk("x.apk", device="d", run=run)
    assert ok
    verbs = ["uninstall" if "uninstall" in a else ("install" if "install" in a else "?") for a in order]
    assert verbs.index("uninstall") < verbs.index("install")

@pytest.mark.skipif(not JDK_OK, reason="JDK jarsigner not found")
def test_ensure_keystore_and_sign(tmp_path):
    ks = tbbuild.ensure_keystore(str(tmp_path / "ks"))
    assert pathlib.Path(ks).exists()
    src = _synthetic_src(tmp_path)
    apk = tbbuild.build_apk(str(tmp_path / "nostage"), str(tmp_path / "u.apk"), src=src)
    signed = tbbuild.sign_apk(apk, ks, str(tmp_path / "s.apk"))
    import subprocess
    v = subprocess.run([tbbuild.JARSIGNER, "-verify", signed], capture_output=True, text=True)
    assert "jar verified" in v.stdout.lower()
