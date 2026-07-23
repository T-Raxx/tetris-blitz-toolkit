import json, pathlib
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QGridLayout, QFileDialog, QCheckBox, QFrame)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import tbdiscover, tbgallery

CATS = ["disabled_powerup", "orphan_sprite", "unused_mode", "event_branded", "db_asset", "sound"]

class DiscoveryTab(QWidget):
    def __init__(self, cache_dir="discovery_cache"):
        super().__init__()
        self.cache_dir = cache_dir
        from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
        self._audio = QAudioOutput(); self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio)
        self.findings = self._load_or_build()

        self.search = QLineEdit(); self.search.setPlaceholderText("search…")
        self.search.textChanged.connect(self._apply_filter)
        self.cat_boxes = {}
        bar = QHBoxLayout(); bar.addWidget(self.search)
        for c in CATS:
            cb = QCheckBox(c); cb.setChecked(True); cb.stateChanged.connect(self._apply_filter)
            self.cat_boxes[c] = cb; bar.addWidget(cb)
        rebuild = QPushButton("Rebuild"); rebuild.clicked.connect(self._rebuild)
        export = QPushButton("Export HTML…"); export.clicked.connect(self._export)
        extractall = QPushButton("Extract all images…"); extractall.clicked.connect(self._extract_all)
        bar.addStretch(1); bar.addWidget(rebuild); bar.addWidget(export); bar.addWidget(extractall)

        self.grid = QGridLayout()
        holder = QWidget(); holder.setLayout(self.grid)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(holder)

        root = QVBoxLayout(self)
        self.count_lbl = QLabel(); root.addLayout(bar); root.addWidget(self.count_lbl); root.addWidget(scroll, 1)
        self.cards = []
        self._populate()

    def _extract_all_dir(self, out_dir):
        import tbextract
        return tbextract.extract_all(out_dir)

    def _extract_all(self):
        from PyQt6.QtWidgets import QMessageBox
        d = QFileDialog.getExistingDirectory(self, "Extract all images to…")
        if not d:
            return
        res = self._extract_all_dir(d)
        self._rebuild()   # refresh catalog (incl. db_asset findings) + cards after extracting
        QMessageBox.information(self, "Extract all images",
            f"{res['count']} images\n"
            f"db={res['by_type']['db']} atlas={res['by_type']['atlas']} loose={res['by_type']['loose']}\n"
            f"errors: {len(res['errors'])}\n→ {res['out_dir']}")

    def _load_or_build(self):
        cat = pathlib.Path(self.cache_dir) / "catalog.json"
        if not cat.exists():
            tbdiscover.build_catalog(self.cache_dir)
        return json.loads(cat.read_text(encoding="utf-8"))["findings"]

    def _populate(self):
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w: w.deleteLater()
        self.cards = []
        for i, f in enumerate(self.findings):
            card = self._make_card(f)
            self.cards.append((card, f))
            self.grid.addWidget(card, i // 6, i % 6)
        self._apply_filter()

    def _make_card(self, f):
        box = QFrame(); box.setFrameShape(QFrame.Shape.StyledPanel)
        lay = QVBoxLayout(box)
        sound_path = f.get("sound_path")
        if sound_path:
            play = QPushButton("▶ Play"); play.clicked.connect(lambda _, p=sound_path: self._play(p))
            lay.addWidget(play)
        else:
            thumbs = f.get("thumbs") or []
            img = QLabel()
            if thumbs and pathlib.Path(thumbs[0]).exists():
                img.setPixmap(QPixmap(thumbs[0]).scaled(56, 56, Qt.AspectRatioMode.KeepAspectRatio))
            else:
                img.setText("—")
            img.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(img)
        t = QLabel(f["title"]); t.setWordWrap(True); lay.addWidget(t)
        colour = "#e06767" if f["status"] == "orphan" else "#8fd18f"
        s = QLabel(f["status"]); s.setStyleSheet(f"color:{colour};font-size:10px"); lay.addWidget(s)
        box.setFixedWidth(150)
        return box

    def _play(self, path):
        from PyQt6.QtCore import QUrl
        self._player.setSource(QUrl.fromLocalFile(path)); self._player.play()

    def _apply_filter(self):
        s = self.search.text().lower()
        on = {c for c, cb in self.cat_boxes.items() if cb.isChecked()}
        shown = 0
        for card, f in self.cards:
            blob = (f["title"] + " " + f["status"] + " " + f["source_file"]).lower()
            vis = f["category"] in on and s in blob
            card.setVisible(vis); shown += vis
        self.count_lbl.setText(f"{shown} / {len(self.cards)} shown")

    def _rebuild(self):
        tbdiscover.build_catalog(self.cache_dir)
        self.findings = self._load_or_build(); self._populate()

    def _export(self):
        p, _ = QFileDialog.getSaveFileName(self, "Export gallery", "discovery.html", "HTML (*.html)")
        if p:
            tbgallery.render_html(self.cache_dir, p)
