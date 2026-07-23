import json, pathlib
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QGridLayout, QFileDialog, QCheckBox, QFrame, QTabWidget, QComboBox, QMessageBox)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import tbdiscover, tbgallery

ASSET_CATS = ["disabled_powerup", "orphan_sprite", "unused_mode", "event_branded", "db_asset"]
STALE_FILES = ["tbdiscover.py", "tbsounds.py", "mosaic_symbols.json"]   # catalog older than these -> rebuild

class AssetsView(QWidget):
    """Image/finding grid with per-category checkboxes + search + build/export/extract actions."""
    def __init__(self, on_rebuild, on_export, on_extract):
        super().__init__()
        self.findings = []; self.cards = []
        self.search = QLineEdit(); self.search.setPlaceholderText("search…")
        self.search.textChanged.connect(self._apply_filter)
        self.cat_boxes = {}
        bar = QHBoxLayout(); bar.addWidget(self.search)
        for c in ASSET_CATS:
            cb = QCheckBox(c); cb.setChecked(True); cb.stateChanged.connect(self._apply_filter)
            self.cat_boxes[c] = cb; bar.addWidget(cb)
        rebuild = QPushButton("Rebuild"); rebuild.clicked.connect(on_rebuild)
        export = QPushButton("Export HTML…"); export.clicked.connect(on_export)
        extractall = QPushButton("Extract all images…"); extractall.clicked.connect(on_extract)
        bar.addStretch(1); bar.addWidget(rebuild); bar.addWidget(export); bar.addWidget(extractall)
        self.grid = QGridLayout(); holder = QWidget(); holder.setLayout(self.grid)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(holder)
        self.count_lbl = QLabel()
        root = QVBoxLayout(self); root.addLayout(bar); root.addWidget(self.count_lbl); root.addWidget(scroll, 1)

    def set_findings(self, findings):
        self.findings = [f for f in findings if f["category"] in ASSET_CATS]
        self._populate()

    def _populate(self):
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w: w.deleteLater()
        self.cards = []
        for i, f in enumerate(self.findings):
            card = self._make_card(f); self.cards.append((card, f)); self.grid.addWidget(card, i // 6, i % 6)
        self._apply_filter()

    def _make_card(self, f):
        box = QFrame(); box.setFrameShape(QFrame.Shape.StyledPanel); lay = QVBoxLayout(box)
        thumbs = f.get("thumbs") or []
        img = QLabel()
        if thumbs and pathlib.Path(thumbs[0]).exists():
            img.setPixmap(QPixmap(thumbs[0]).scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            img.setText("—")
        img.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(img)
        t = QLabel(f["title"]); t.setWordWrap(True); lay.addWidget(t)
        s = QLabel(f["status"]); s.setStyleSheet("color:#8fd18f;font-size:10px"); lay.addWidget(s)
        box.setFixedWidth(150); return box

    def _apply_filter(self):
        s = self.search.text().lower()
        on = {c for c, cb in self.cat_boxes.items() if cb.isChecked()}
        shown = 0
        for card, f in self.cards:
            blob = (f["title"] + " " + f["status"] + " " + f["source_file"]).lower()
            vis = f["category"] in on and s in blob
            card.setVisible(vis); shown += vis
        self.count_lbl.setText(f"{shown} / {len(self.cards)} shown")

class SoundsView(QWidget):
    """Dedicated sound browser: search + referenced/orphan filter + in-tab ▶ playback."""
    def __init__(self, play):
        super().__init__()
        self.play = play; self.findings = []; self.cards = []
        self.search = QLineEdit(); self.search.setPlaceholderText("search sounds…")
        self.search.textChanged.connect(self._apply_filter)
        self.show_pick = QComboBox(); self.show_pick.addItems(["all", "referenced", "orphan"])
        self.show_pick.currentTextChanged.connect(self._apply_filter)
        bar = QHBoxLayout(); bar.addWidget(self.search)
        bar.addWidget(QLabel("show")); bar.addWidget(self.show_pick); bar.addStretch(1)
        self.grid = QGridLayout(); holder = QWidget(); holder.setLayout(self.grid)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(holder)
        self.count_lbl = QLabel()
        root = QVBoxLayout(self); root.addLayout(bar); root.addWidget(self.count_lbl); root.addWidget(scroll, 1)

    def set_findings(self, findings):
        self.findings = [f for f in findings if f["category"] == "sound"]
        self._populate()

    def _populate(self):
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w: w.deleteLater()
        self.cards = []
        for i, f in enumerate(self.findings):
            card = self._make_card(f); self.cards.append((card, f)); self.grid.addWidget(card, i // 6, i % 6)
        self._apply_filter()

    def _make_card(self, f):
        box = QFrame(); box.setFrameShape(QFrame.Shape.StyledPanel); lay = QVBoxLayout(box)
        play = QPushButton("▶ Play"); play.clicked.connect(lambda _, p=f["sound_path"]: self.play(p))
        lay.addWidget(play)
        t = QLabel(f["title"]); t.setWordWrap(True); lay.addWidget(t)
        colour = "#e06767" if f["status"] == "orphan" else "#8fd18f"
        s = QLabel(f["status"]); s.setStyleSheet(f"color:{colour};font-size:10px"); lay.addWidget(s)
        box.setFixedWidth(150); return box

    def _apply_filter(self):
        s = self.search.text().lower(); show = self.show_pick.currentText()
        shown = 0
        for card, f in self.cards:
            vis = s in f["title"].lower() and (show == "all" or f["status"] == show)
            card.setVisible(vis); shown += vis
        self.count_lbl.setText(f"{shown} / {len(self.cards)} shown")

class DiscoveryTab(QWidget):
    def __init__(self, cache_dir="discovery_cache"):
        super().__init__()
        self.cache_dir = cache_dir
        from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
        self._audio = QAudioOutput(); self._player = QMediaPlayer(); self._player.setAudioOutput(self._audio)
        self.assets = AssetsView(self._rebuild, self._export, self._extract_all)
        self.sounds = SoundsView(self._play)
        self.subtabs = QTabWidget()
        self.subtabs.addTab(self.assets, "Assets"); self.subtabs.addTab(self.sounds, "Sounds")
        root = QVBoxLayout(self); root.addWidget(self.subtabs)
        self.findings = []
        self._load_catalog(build_if_missing=True)

    def _catalog_path(self):
        return pathlib.Path(self.cache_dir) / "catalog.json"

    def _load_catalog(self, build_if_missing=False):
        cat = self._catalog_path()
        if build_if_missing and not cat.exists():
            tbdiscover.build_catalog(self.cache_dir)
        if cat.exists():
            self.findings = json.loads(cat.read_text(encoding="utf-8"))["findings"]
        self.assets.set_findings(self.findings); self.sounds.set_findings(self.findings)

    def ensure_fresh(self):
        """Auto-rebuild on open when the catalog is missing or older than a detector file."""
        cat = self._catalog_path()
        newest = 0.0
        for f in STALE_FILES:
            p = pathlib.Path(f)
            if p.exists():
                newest = max(newest, p.stat().st_mtime)
        if (not cat.exists()) or (cat.stat().st_mtime < newest):
            tbdiscover.build_catalog(self.cache_dir)
        self._load_catalog()

    def _rebuild(self):
        tbdiscover.build_catalog(self.cache_dir); self._load_catalog()

    def _play(self, path):
        from PyQt6.QtCore import QUrl
        self._player.setSource(QUrl.fromLocalFile(path)); self._player.play()

    def _extract_all_dir(self, out_dir):
        import tbextract
        return tbextract.extract_all(out_dir)

    def _extract_all(self):
        d = QFileDialog.getExistingDirectory(self, "Extract all images to…")
        if not d:
            return
        res = self._extract_all_dir(d)
        self._rebuild()
        QMessageBox.information(self, "Extract all images",
            f"{res['count']} images\n"
            f"db={res['by_type']['db']} atlas={res['by_type']['atlas']} loose={res['by_type']['loose']}\n"
            f"errors: {len(res['errors'])}\n→ {res['out_dir']}")

    def _export(self):
        p, _ = QFileDialog.getSaveFileName(self, "Export gallery", "discovery.html", "HTML (*.html)")
        if p:
            tbgallery.render_html(self.cache_dir, p)
