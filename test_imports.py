"""Cross-platform smoke test: every module imports cleanly WITHOUT the EA key or APK assets.
This is what CI runs on Windows + macOS — modules must not touch proprietary assets at import
time. Asset-dependent behavior is covered by the other tests, which run locally where the
user has their own game files."""
import os, sys, pathlib, importlib
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "apkbuilder"))

CORE = ["tbcrypt", "tbfiles", "tbadb", "tbmosaic", "tbassets", "tbatlas", "tbassembler",
        "tbpanels", "tbdiscover", "tbgallery", "tbbuild", "tbmods", "tbmodbuilder",
        "tbrestore", "tbrestoretab", "tbnative", "tbnativetab", "tbrawview", "tbinject",
        "tbinjecttab", "tbsave", "tbsavetab", "tbsemantics", "tbsounds", "tbextract",
        "tbdiscovertab", "apkbuild"]

def test_core_modules_import():
    for m in CORE:
        importlib.import_module(m)

def test_editor_and_tabs_import():
    from PyQt6.QtWidgets import QApplication
    QApplication.instance() or QApplication([])
    import tb_editor
    assert hasattr(tb_editor, "Editor") and hasattr(tb_editor, "main")

def test_build_tools_resolve_cross_platform():
    import tbbuild, apkbuild
    # _jtool / _java always return a string (a resolved path or the bare name); never crash
    assert isinstance(tbbuild._jtool("jarsigner"), str)
    assert isinstance(apkbuild._java(), str)

def test_save_base_dir_from_env():
    import importlib, tbsave
    orig = os.environ.get("TB_SAVE_DIR")     # preserve the shell's value (used by other tests)
    try:
        os.environ["TB_SAVE_DIR"] = "some/custom/dir"
        importlib.reload(tbsave)
        assert str(tbsave.BASE_DIR) == str(pathlib.Path("some/custom/dir"))
    finally:
        if orig is None:
            os.environ.pop("TB_SAVE_DIR", None)
        else:
            os.environ["TB_SAVE_DIR"] = orig
        importlib.reload(tbsave)              # restore module global with the original env

