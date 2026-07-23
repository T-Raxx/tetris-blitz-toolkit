import pathlib
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QComboBox,
    QPushButton, QScrollArea, QGridLayout, QFrame)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import tbrestore, tbassets

BADGE = {"works": "#8fd18f", "crashes": "#e06767", "untested": "#999999"}

class RestoreTab(QWidget):
    def __init__(self, key, on_build, cache_dir="discovery_cache"):
        super().__init__()
        self.key, self.on_build, self.cache_dir = key, on_build, cache_dir
        self.catalog = tbrestore.restore_catalog(key)
        self._icons = self._extract_icons()

        top = QHBoxLayout()
        restoreb = QPushButton("Restore selected → Build & Install")
        restoreb.clicked.connect(self._restore)
        top.addWidget(QLabel(f"{len(self.catalog)} disabled powerups/finishers"))
        top.addStretch(1); top.addWidget(restoreb)

        grid = QGridLayout(); holder = QWidget(); holder.setLayout(grid)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(holder)

        self.cards = []
        for i, c in enumerate(self.catalog):
            grid.addWidget(self._make_card(c), i // 4, i % 4)

        root = QVBoxLayout(self); root.addLayout(top); root.addWidget(scroll, 1)

    def _extract_icons(self):
        names = [f'Common/{c["icon"]}.png' for c in self.catalog if c.get("icon")]
        try:
            return {pathlib.Path(p).stem: p
                    for p in tbassets.extract_named(str(pathlib.Path(self.cache_dir) / "restore"), names).values()}
        except Exception:
            return {}

    def _make_card(self, c):
        box = QFrame(); box.setFrameShape(QFrame.Shape.StyledPanel); box.setFixedWidth(180)
        lay = QVBoxLayout(box)
        img = QLabel(); path = self._icons.get(c.get("icon") or "")
        if path and pathlib.Path(path).exists():
            img.setPixmap(QPixmap(path).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            img.setText("—")
        img.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(img)
        name = QLabel(tbrestore._base_name(c.get("icon"))); name.setWordWrap(True); lay.addWidget(name)
        badge = QLabel(c["status"]); badge.setStyleSheet(f'color:{BADGE.get(c["status"],"#999")};font-size:10px')
        lay.addWidget(badge)
        combo = QComboBox(); combo.addItems(["untested", "works", "crashes"])
        combo.setCurrentText(c["status"])
        def on_status(s, uid=c["uId"], b=badge):
            tbrestore.set_status(uid, s); b.setText(s); b.setStyleSheet(f'color:{BADGE.get(s,"#999")};font-size:10px')
        combo.currentTextChanged.connect(on_status); lay.addWidget(combo)
        cb = QCheckBox("restore"); lay.addWidget(cb)
        self.cards.append((c["uId"], cb))
        return box

    def selection(self):
        return [uid for uid, cb in self.cards if cb.isChecked()]

    def _restore(self):
        self.on_build(self.selection())
