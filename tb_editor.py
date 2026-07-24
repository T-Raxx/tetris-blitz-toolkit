import sys, pathlib, json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QPlainTextEdit, QPushButton, QLabel, QTabWidget, QFileDialog, QMessageBox, QSplitter,
    QScrollArea)
from PyQt6.QtCore import Qt
import tbfiles, tbadb, tbcrypt, tbpanels, tbmosaic, tbassembler, tbdiscovertab, tbbuild, tbmods, tbmodbuilder, tbrestore, tbrestoretab, tbnative, tbnativetab, tbrawview, tbinject, tbinjecttab, tbsavetab, tbkeyfind

COEFF_DIR = pathlib.Path("..") / "Tetris blitz" / "assets" / "Assets" / "Coefficients"
DARK = """
QWidget{background:#1e1f26;color:#e6e6e6;font-size:13px}
QListWidget,QPlainTextEdit{background:#15161c;border:1px solid #2c2e38;border-radius:6px}
QPushButton{background:#3a3d4d;border:0;padding:7px 12px;border-radius:6px}
QPushButton:hover{background:#4a4e63}
QPushButton:disabled{background:#26283040;color:#666}
QTabBar::tab{background:#23252f;padding:7px 14px;border-top-left-radius:6px;border-top-right-radius:6px}
QTabBar::tab:selected{background:#3a3d4d}
QLabel#status{color:#8fd18f}
"""

class Editor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tetris Blitz — File Editor")
        self.resize(1100, 720)
        self.key = self._ensure_key()
        self.current = None
        self.current_path = None
        self.mod_stage = "mod_stage"

        self.files = QListWidget()
        self._load_local_list()
        self.files.itemActivated.connect(lambda it: self.open_local(str(COEFF_DIR / it.text())))

        self.raw = tbrawview.RawJsonView()
        self.tabs = QTabWidget()
        self.smart_holder = QWidget(); self.smart_holder.setLayout(QVBoxLayout())
        smart_scroll = QScrollArea(); smart_scroll.setWidgetResizable(True); smart_scroll.setWidget(self.smart_holder)
        self.tabs.addTab(smart_scroll, "Smart")
        self.tabs.addTab(self.raw, "Raw JSON")
        self._discovery = None
        self._disc_placeholder = QWidget()
        self.tabs.addTab(self._disc_placeholder, "Discovery")
        self.mod_tab = tbmodbuilder.ModBuilderTab(self.key, self._on_mod_build)
        self.restore_tab = tbrestoretab.RestoreTab(self.key, self._on_restore_build)
        self.native_tab = tbnativetab.NativeTab(self._on_native_build)
        self.inject_tab = tbinjecttab.InjectTab(self._on_inject_build)
        self.save_tab = tbsavetab.SaveTab(self.key)
        self.tabs.addTab(self.mod_tab, "Mod Builder")
        self.tabs.addTab(self.restore_tab, "Restore")
        self.tabs.addTab(self.native_tab, "Native")
        self.tabs.addTab(self.inject_tab, "Inject")
        self.tabs.addTab(self.save_tab, "Save")
        self._staged = {}          # rel-path -> bytes, for files staged via "Stage for build"
        self.tabs.currentChanged.connect(self._maybe_build_discovery)

        keyb = QPushButton("Extract key"); keyb.clicked.connect(self._extract_key)
        keyb.setToolTip("Recover the AES key from YOUR game files (lib .so + a coefficient). "
                        "Runs automatically on first launch if key.json is missing.")
        openb = QPushButton("Open…"); openb.clicked.connect(self._open_dialog)
        saveb = QPushButton("Save As…"); saveb.clicked.connect(self._save_dialog)
        self.pullb = QPushButton("Pull save"); self.pushb = QPushButton("Push save")
        self.badge = QLabel("—"); self.status = QLabel("ready"); self.status.setObjectName("status")

        stageb = QPushButton("Stage for build"); stageb.clicked.connect(self._stage_current)
        buildb = QPushButton("Build & Install APK"); buildb.clicked.connect(self._build_install)
        buildb.setToolTip("Applies EVERYTHING selected across all tabs (staged files + Mod Builder + "
                          "Native patches + Restore + Inject) into one fresh build, then installs via adb.")
        redistb = QPushButton("Build Redistributable APK"); redistb.clicked.connect(self._build_redist)
        redistb.setToolTip("Applies EVERY tab's mods, then produces a v2+ signed APK for real "
                           "non-rooted hardware (does NOT install — share the file).")
        top = QHBoxLayout()
        for wdg in (keyb, openb, saveb, self.pullb, self.pushb, stageb, buildb, redistb, QLabel("fmt:"), self.badge):
            top.addWidget(wdg)
        top.addStretch(1); top.addWidget(self.status)

        split = QSplitter()
        split.addWidget(self.files); split.addWidget(self.tabs)
        split.setStretchFactor(1, 1); split.setSizes([260, 840])

        root = QWidget(); lay = QVBoxLayout(root)
        lay.addLayout(top); lay.addWidget(split, 1)
        self.setCentralWidget(root)
        self.setStyleSheet(DARK)
        self.pullb.clicked.connect(self._pull); self.pushb.clicked.connect(self._push)
        self._refresh_device()

    def _load_local_list(self):
        self.files.clear()
        for p in sorted(COEFF_DIR.glob("*.json")):
            self.files.addItem(p.name)

    def open_local(self, path):
        try:
            tb = tbfiles.load_path(path, self.key)
        except Exception as e:
            QMessageBox.warning(self, "Open failed", f"Not a TB file?\n{e}"); return
        self.current, self.current_path = tb, path
        self.badge.setText(tb.fmt)
        self.raw.setPlainText(json.dumps(tb.obj, indent=2))
        self._rebuild_smart()
        self.status.setText(f"opened {pathlib.Path(path).name}")
        self._verify_roundtrip()

    def _sync_raw_to_obj(self):
        if self.current and self.tabs.currentWidget() is self.raw:
            self.current.obj = json.loads(self.raw.toPlainText())

    def save_local(self, path):
        self._sync_raw_to_obj()
        tbfiles.dump_path(self.current, path)
        self.status.setText(f"saved {pathlib.Path(path).name}")

    def _open_dialog(self):
        p, _ = QFileDialog.getOpenFileName(self, "Open TB file", str(COEFF_DIR))
        if p: self.open_local(p)

    def _save_dialog(self):
        if not self.current: return
        p, _ = QFileDialog.getSaveFileName(self, "Save encrypted", self.current_path or "")
        if p:
            try: self.save_local(p)
            except Exception as e: QMessageBox.warning(self, "Save failed", str(e))

    def _maybe_build_discovery(self, idx):
        if self.tabs.tabText(idx) != "Discovery":
            return
        if self._discovery is None:
            self.status.setText("building discovery catalog…"); QApplication.processEvents()
            self._discovery = tbdiscovertab.DiscoveryTab()
            self.tabs.removeTab(idx); self.tabs.insertTab(idx, self._discovery, "Discovery")
            self.tabs.setCurrentIndex(idx)
        self._discovery.ensure_fresh()   # auto-rebuild on open when stale
        self.status.setText("discovery ready")

    def _rebuild_smart(self):
        holder = self.smart_holder.layout()
        while holder.count():
            w = holder.takeAt(0).widget()
            if w: w.deleteLater()
        if not self.current: return
        def on_change():
            self.raw.blockSignals(True)
            self.raw.setPlainText(json.dumps(self.current.obj, indent=2))
            self.raw.blockSignals(False)
            self.status.setText("edited (unsaved)")
        if tbmosaic.is_mosaic(self.current.obj):
            holder.addWidget(tbassembler.Assembler(self.current, on_change, name=self.current_path))
        else:
            holder.addWidget(tbpanels.build_smart(self.current, on_change))

    def _refresh_device(self):
        try:
            dev = tbadb.device()
        except Exception:
            dev = None
        ok = dev is not None
        self.pullb.setEnabled(ok); self.pushb.setEnabled(ok)
        self.status.setText(f"device: {dev}" if ok else "device: none")

    def _pull(self):
        try:
            data = tbadb.pull(tbadb.KNOWN_FILES[0])
            tb = tbfiles.load_bytes(data, self.key)
        except Exception as e:
            QMessageBox.warning(self, "Pull failed", str(e)); return
        self.current, self.current_path = tb, tbadb.KNOWN_FILES[0]
        self.badge.setText(tb.fmt)
        self.raw.setPlainText(json.dumps(tb.obj, indent=2))
        self._rebuild_smart()
        self.status.setText("pulled live save")
        self._verify_roundtrip()

    def _push(self):
        if not self.current: return
        self._sync_raw_to_obj()
        try:
            data = tbfiles.dump_bytes(self.current)
            bak = tbadb.push(tbadb.KNOWN_FILES[0], data)
        except Exception as e:
            QMessageBox.warning(self, "Push failed", str(e)); return
        QMessageBox.information(self, "Pushed", f"Save pushed.\nBackup: {bak or '(none)'}")
        self.status.setText("pushed save (restart game to load)")

    def _stage_current(self):
        if not self.current:
            return
        self._sync_raw_to_obj()
        src = (pathlib.Path("..") / "Tetris blitz").resolve()
        try:
            rel = pathlib.Path(self.current_path).resolve().relative_to(src)
        except Exception:
            QMessageBox.warning(self, "Stage", "Only files from the APK tree can be staged "
                                "(device saves use Push)."); return
        dest = pathlib.Path(self.mod_stage) / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = tbfiles.dump_bytes(self.current)
        dest.write_bytes(data)
        self._staged[rel.as_posix()] = data          # remember for the unified build
        n = sum(1 for p in pathlib.Path(self.mod_stage).rglob("*") if p.is_file())
        self.status.setText(f"staged {rel.name} ({n} file(s) in build)")

    def _stage_all(self):
        """Fresh mod_stage with EVERYTHING selected across tabs: staged files + Mod Builder config +
        Native patches + Restore. Returns the applied-labels list."""
        import shutil
        if pathlib.Path(self.mod_stage).exists():
            shutil.rmtree(self.mod_stage)
        applied = []
        for rel, data in self._staged.items():        # re-stage manual file edits (matrix etc)
            dest = pathlib.Path(self.mod_stage) / rel
            dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(data)
            applied.append(f"file:{pathlib.Path(rel).name}")
        applied += tbmods.apply_and_stage(self.mod_tab._build_config(), self.mod_stage, self.key)["applied"]
        ids, vals = self.native_tab.selection()
        if ids:
            applied += tbnative.stage_native(ids, tbnative.load_patches(), self.mod_stage, values=vals)["applied"]
        uIds = self.restore_tab.selection()
        if uIds:
            applied += [f"restore:{u}" for u in tbrestore.apply_restore(uIds, self.mod_stage, self.key)["restored"]]
        injs = self.inject_tab.selection()
        if injs:
            applied += tbinject.stage_injections(injs, self.mod_stage)["applied"]
        return applied

    def _build_install(self):
        """The main build: applies everything selected across all tabs into one fresh build."""
        self.status.setText("staging all tabs + building…"); QApplication.processEvents()
        try:
            applied = self._stage_all()
            res = tbbuild.build_sign_install(self.mod_stage)
        except Exception as e:
            QMessageBox.warning(self, "Build failed", str(e)); return
        QMessageBox.information(self, "Build & Install",
            f"applied ({len(applied)}): {applied}\ninstalled = {res['installed']}\n\n{res['log'][-400:]}")
        self.status.setText("installed ✓" if res["installed"] else "install failed")

    def _ensure_key(self):
        """Load key.json, or auto-extract the AES key from the user's OWN game files on first run
        (no EA secret is shipped). Returns the key dict, or None if the game files aren't present."""
        if pathlib.Path("key.json").exists():
            try:
                return tbcrypt.load_key("key.json")
            except Exception:
                pass
        try:
            tbkeyfind.extract_from_game()
            return tbcrypt.load_key("key.json")
        except Exception:
            return None

    def _extract_key(self):
        """Manual (re)extraction — e.g. after pointing at a different game copy."""
        self.status.setText("extracting AES key from game files…"); QApplication.processEvents()
        try:
            r = tbkeyfind.extract_from_game()
            self.key = tbcrypt.load_key("key.json")
        except Exception as e:
            QMessageBox.warning(self, "Extract key", f"Could not extract key:\n{e}\n\n"
                                "Point --so/--coeff at your unpacked game, or run "
                                "`python tbkeyfind.py`."); return
        QMessageBox.information(self, "Extract key", f"key.json written (AES found: {r['aes']}).\n"
                               "Reopen a file / tab to use it.")
        self.status.setText("key extracted ✓")

    def _apkbuild_module(self):
        """Import the standalone apkbuilder (repo subfolder; falls back to a sibling folder)."""
        import sys as _sys
        here = pathlib.Path(__file__).resolve().parent
        for cand in (here / "apkbuilder", here.parent / "apkbuilder"):
            if (cand / "apkbuild.py").exists():
                if str(cand) not in _sys.path:
                    _sys.path.insert(0, str(cand))
                break
        import apkbuild
        return apkbuild

    def _build_redist(self):
        """Stage every tab's mods, then produce a v2+ signed redistributable APK (no install)."""
        self.status.setText("staging all tabs + building redistributable APK…"); QApplication.processEvents()
        try:
            applied = self._stage_all()
            apkbuild = self._apkbuild_module()
            res = apkbuild.build(str(pathlib.Path(self.mod_stage).resolve()),
                                 "dist/tetrisblitz-modded.apk")
        except Exception as e:
            QMessageBox.warning(self, "Redistributable build failed", str(e)); return
        QMessageBox.information(self, "Redistributable APK",
            f"applied ({len(applied)}): {applied}\n\nAPK: {res['apk']}\nsha256: {res['sha256']}\n"
            f"signed(v1+v2+v3): {res['signed']}\n\nInstalable en hardware non-rooted. Compartí el archivo.")
        self.status.setText("redistributable APK ready ✓" if res["signed"] else "APK built (unsigned)")

    # Every tab's "Apply + Build & Install" performs the SAME unified build (all tabs' selections).
    def _on_mod_build(self, config=None): self._build_install()
    def _on_native_build(self, ids=None, values=None): self._build_install()
    def _on_restore_build(self, uIds=None): self._build_install()
    def _on_inject_build(self, injs=None): self._build_install()

    def _verify_roundtrip(self):
        if not self.current: return
        try:
            data = tbfiles.dump_bytes(self.current)
            reparsed = tbfiles.load_bytes(data, self.key)
            good = reparsed.obj == self.current.obj
            self.badge.setText(f"{self.current.fmt}  {'✓' if good else '✗'}")
        except Exception:
            self.badge.setText(f"{self.current.fmt}  ?")

def main():
    app = QApplication(sys.argv)
    Editor().show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
