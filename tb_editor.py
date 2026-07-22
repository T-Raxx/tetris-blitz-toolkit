import sys, pathlib, json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QPlainTextEdit, QPushButton, QLabel, QTabWidget, QFileDialog, QMessageBox, QSplitter)
from PyQt6.QtCore import Qt
import tbfiles, tbadb, tbcrypt, tbpanels, tbmosaic, tbassembler, tbdiscovertab, tbbuild, tbmods, tbmodbuilder, tbrestore, tbrestoretab, tbnative, tbnativetab

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
        self.key = tbcrypt.load_key("key.json")
        self.current = None
        self.current_path = None
        self.mod_stage = "mod_stage"

        self.files = QListWidget()
        self._load_local_list()
        self.files.itemActivated.connect(lambda it: self.open_local(str(COEFF_DIR / it.text())))

        self.raw = QPlainTextEdit(); self.raw.setTabStopDistance(28)
        self.tabs = QTabWidget()
        self.smart_holder = QWidget(); self.smart_holder.setLayout(QVBoxLayout())
        self.tabs.addTab(self.smart_holder, "Smart")
        self.tabs.addTab(self.raw, "Raw JSON")
        self._discovery = None
        self._disc_placeholder = QWidget()
        self.tabs.addTab(self._disc_placeholder, "Discovery")
        self.tabs.addTab(tbmodbuilder.ModBuilderTab(self.key, self._on_mod_build), "Mod Builder")
        self.tabs.addTab(tbrestoretab.RestoreTab(self.key, self._on_restore_build), "Restore")
        self.tabs.addTab(tbnativetab.NativeTab(self._on_native_build), "Native")
        self.tabs.currentChanged.connect(self._maybe_build_discovery)

        openb = QPushButton("Open…"); openb.clicked.connect(self._open_dialog)
        saveb = QPushButton("Save As…"); saveb.clicked.connect(self._save_dialog)
        self.pullb = QPushButton("Pull save"); self.pushb = QPushButton("Push save")
        self.badge = QLabel("—"); self.status = QLabel("ready"); self.status.setObjectName("status")

        stageb = QPushButton("Stage for build"); stageb.clicked.connect(self._stage_current)
        buildb = QPushButton("Build & Install APK"); buildb.clicked.connect(self._build_install)
        top = QHBoxLayout()
        for wdg in (openb, saveb, self.pullb, self.pushb, stageb, buildb, QLabel("fmt:"), self.badge):
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
        if self.tabs.tabText(idx) != "Discovery" or self._discovery is not None:
            return
        self.status.setText("building discovery catalog…"); QApplication.processEvents()
        self._discovery = tbdiscovertab.DiscoveryTab()
        self.tabs.removeTab(idx); self.tabs.insertTab(idx, self._discovery, "Discovery")
        self.tabs.setCurrentIndex(idx); self.status.setText("discovery ready")

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
            holder.addWidget(tbassembler.Assembler(self.current, on_change))
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
        dest.write_bytes(tbfiles.dump_bytes(self.current))
        n = sum(1 for p in pathlib.Path(self.mod_stage).rglob("*") if p.is_file())
        self.status.setText(f"staged {rel.name} ({n} file(s) in build)")

    def _build_install(self):
        self.status.setText("building + signing + installing…"); QApplication.processEvents()
        try:
            res = tbbuild.build_sign_install(self.mod_stage)
        except Exception as e:
            QMessageBox.warning(self, "Build failed", str(e)); return
        QMessageBox.information(self, "Build & Install",
            f"installed = {res['installed']}\n\n{res['log'][-500:]}")
        self.status.setText("installed ✓" if res["installed"] else "install failed")

    def _on_mod_build(self, config):
        self.status.setText("applying mods + building…"); QApplication.processEvents()
        try:
            staged = tbmods.apply_and_stage(config, self.mod_stage, self.key)
            res = tbbuild.build_sign_install(self.mod_stage)
        except Exception as e:
            QMessageBox.warning(self, "Mod build failed", str(e)); return
        QMessageBox.information(self, "Mod Builder",
            f"applied: {staged['applied']}\ninstalled = {res['installed']}\n\n{res['log'][-400:]}")
        self.status.setText("mods installed ✓" if res["installed"] else "install failed")

    def _on_native_build(self, ids):
        if not ids:
            QMessageBox.information(self, "Native", "No patches selected."); return
        self.status.setText("patching .so + building…"); QApplication.processEvents()
        try:
            staged = tbnative.stage_native(ids, tbnative.load_patches(), self.mod_stage)
            build = tbbuild.build_sign_install(self.mod_stage)
        except Exception as e:
            QMessageBox.warning(self, "Native build failed", str(e)); return
        QMessageBox.information(self, "Native",
            f"applied: {staged['applied']}\ninstalled = {build['installed']}\n\n{build['log'][-300:]}")
        self.status.setText("native patched ✓" if build["installed"] else "install failed")

    def _on_restore_build(self, uIds):
        if not uIds:
            QMessageBox.information(self, "Restore", "No items selected."); return
        self.status.setText("restoring + building…"); QApplication.processEvents()
        try:
            res = tbrestore.apply_restore(uIds, self.mod_stage, self.key)
            build = tbbuild.build_sign_install(self.mod_stage)
        except Exception as e:
            QMessageBox.warning(self, "Restore build failed", str(e)); return
        QMessageBox.information(self, "Restore",
            f"restored: {res['restored']}\ncrashers labeled: {res['labeled_crashers']}\n"
            f"installed = {build['installed']}\n\n{build['log'][-300:]}")
        self.status.setText("restored ✓" if build["installed"] else "install failed")

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
