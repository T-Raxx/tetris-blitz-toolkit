import sys, pathlib, zipfile, types
_APK = str((pathlib.Path(__file__).resolve().parent / "apkbuilder"))
if _APK not in sys.path:
    sys.path.insert(0, _APK)
import apkbuild

def _tree(tmp):
    src = tmp / "src"; stage = tmp / "stage"
    for rel, data in [("resources.arsc", b"ARSC"), ("lib/arm64-v8a/x.so", b"SO"),
                      ("assets/a.txt", b"orig"), ("META-INF/CERT.SF", b"sig")]:
        p = src / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
    for rel, data in [("assets/a.txt", b"MODDED"), ("assets/new.txt", b"NEW")]:
        p = stage / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
    return src, stage

def test_stored_rule():
    assert apkbuild._stored("resources.arsc") and apkbuild._stored("lib/arm64-v8a/x.so")
    assert not apkbuild._stored("assets/a.txt")

def test_repack_overrides_new_files_and_drops_metainf(tmp_path):
    src, stage = _tree(tmp_path)
    out = tmp_path / "out.apk"
    apkbuild.repack(stage, out, src=src)
    with zipfile.ZipFile(out) as z:
        names = set(z.namelist())
        assert z.read("assets/a.txt") == b"MODDED"        # override applied
        assert z.read("assets/new.txt") == b"NEW"          # mod-only file added
        assert not any(n.startswith("META-INF/") for n in names)   # signature dropped
        assert z.getinfo("resources.arsc").compress_type == zipfile.ZIP_STORED
        assert z.getinfo("lib/arm64-v8a/x.so").compress_type == zipfile.ZIP_STORED
        assert z.getinfo("assets/a.txt").compress_type == zipfile.ZIP_DEFLATED

def test_build_unsigned(tmp_path):
    src, stage = _tree(tmp_path)
    res = apkbuild.build(stage, out_apk=str(tmp_path / "u.apk"), src=src, do_sign=False)
    assert res["signed"] is False and len(res["sha256"]) == 64
    assert pathlib.Path(res["apk"]).exists()

def test_build_signed_uses_uber(tmp_path, monkeypatch):
    src, stage = _tree(tmp_path)
    calls = []
    def fake_run(args, **k):
        calls.append(args)
        return types.SimpleNamespace(stdout="APK signature verified", stderr="", returncode=0)
    monkeypatch.setattr(apkbuild, "ensure_uber", lambda: "fake-uber.jar")
    res = apkbuild.build(stage, out_apk=str(tmp_path / "s.apk"), src=src, do_sign=True, run=fake_run)
    assert res["signed"] is True and "verified" in res["verify"]
    assert any("--apks" in c and "-jar" in c for c in calls)          # uber invoked
    assert any("--verify" in c for c in calls)                        # verification ran
