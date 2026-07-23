from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QListWidget, QListWidgetItem, QFileDialog)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import QSize, Qt
import pathlib, tbinject, tbmosaic

CACHE = "assets_cache"
CUSTOM = "Custom PNG…"

class InjectTab(QWidget):
    """Nivel 3 — paint any image over a base-color mino frame in Common0.png."""
    def __init__(self, on_build):
        super().__init__()
        self.on_build = on_build
        self.injs = []                                   # [{"base","source","label"}]
        self.custom_path = None
        try:
            self.catalog = tbinject.catalog_sources(CACHE)
        except Exception:
            self.catalog = {}

        root = QVBoxLayout(self)
        root.addWidget(QLabel("Inyectar mino (Nivel 3)"))
        note = QLabel("Sobrescribe los píxeles del frame de un color base en Common0.png con la "
                      "imagen fuente. Ese color pasa a mostrar la imagen — in-game Y en matrices. "
                      "Reversible (mod de asset). Afecta ese color globalmente, incl. gameplay.")
        note.setWordWrap(True); note.setStyleSheet("color:#9aa;font-size:11px")
        root.addWidget(note)

        colors = tbmosaic.symbols("colors")
        self.base = QComboBox()
        for ch, frame in tbinject.base_targets().items():
            self.base.addItem(f"{ch}  {colors.get(ch, {}).get('name', ch)}", ch)

        self.source = QComboBox()
        for label in self.catalog:
            self.source.addItem(label, label)
        self.source.addItem(CUSTOM, CUSTOM)
        self.source.currentIndexChanged.connect(self._on_source_change)

        self.preview = QLabel(); self.preview.setFixedSize(54, 54)
        self.preview.setStyleSheet("border:1px solid #2c2e38;background:#15161c")

        row = QHBoxLayout()
        row.addWidget(QLabel("base")); row.addWidget(self.base)
        row.addWidget(QLabel("←")); row.addWidget(self.source, 1)
        row.addWidget(self.preview)
        addb = QPushButton("Add"); addb.clicked.connect(self._add); row.addWidget(addb)
        root.addLayout(row)

        self.list = QListWidget(); root.addWidget(self.list, 1)
        row2 = QHBoxLayout()
        rmb = QPushButton("Remove selected"); rmb.clicked.connect(self._remove)
        applyb = QPushButton("Apply injections → Build & Install"); applyb.clicked.connect(self._apply)
        row2.addWidget(rmb); row2.addStretch(1); row2.addWidget(applyb)
        root.addLayout(row2)
        self._refresh_preview()

    def _current_source(self):
        """(label, path) for the selected source, or (None, None). Prompts for custom file."""
        sel = self.source.currentData()
        if sel == CUSTOM:
            return ("custom", self.custom_path)
        return (sel, self.catalog.get(sel))

    def _on_source_change(self):
        if self.source.currentData() == CUSTOM:
            p, _ = QFileDialog.getOpenFileName(self, "Choose PNG", "", "Images (*.png *.jpg *.jpeg)")
            self.custom_path = p or None
        self._refresh_preview()

    def _refresh_preview(self):
        _, path = self._current_source()
        if path and pathlib.Path(path).exists():
            px = QPixmap(path).scaled(54, 54, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
            self.preview.setPixmap(px)
        else:
            self.preview.clear()

    def _add(self):
        ch = self.base.currentData()
        label, path = self._current_source()
        if not path or not pathlib.Path(path).exists():
            return
        self.injs = [j for j in self.injs if j["base"] != ch]    # one injection per base color
        name = "custom" if label == "custom" else label
        self.injs.append({"base": ch, "source": path, "label": name})
        self._rebuild_list()

    def _remove(self):
        for it in self.list.selectedItems():
            ch = it.data(Qt.ItemDataRole.UserRole)
            self.injs = [j for j in self.injs if j["base"] != ch]
        self._rebuild_list()

    def _rebuild_list(self):
        self.list.clear()
        for j in self.injs:
            it = QListWidgetItem(f"{j['base']}  ←  {j['label']}")
            it.setData(Qt.ItemDataRole.UserRole, j["base"])
            if pathlib.Path(j["source"]).exists():
                it.setIcon(QIcon(QPixmap(j["source"])))
            self.list.addItem(it)

    def selection(self):
        return [{"base": j["base"], "source": j["source"]} for j in self.injs]

    def _apply(self):
        self.on_build()
