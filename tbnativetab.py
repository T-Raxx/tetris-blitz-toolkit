from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton,
    QScrollArea, QFrame)
import tbnative

BADGE = {"works": "#8fd18f", "wip": "#d9b45a", "crashes": "#e06767"}

class NativeTab(QWidget):
    def __init__(self, on_build):
        super().__init__()
        self.on_build = on_build
        self.patches = tbnative.load_patches()
        top = QHBoxLayout()
        applyb = QPushButton("Apply patches → Build & Install"); applyb.clicked.connect(self._apply)
        top.addWidget(QLabel(f"{len(self.patches)} native patch(es)")); top.addStretch(1); top.addWidget(applyb)
        col = QVBoxLayout(); holder = QWidget(); holder.setLayout(col)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(holder)
        self.boxes = []
        for p in self.patches:
            row = QFrame(); row.setFrameShape(QFrame.Shape.StyledPanel); rl = QVBoxLayout(row)
            cb = QCheckBox(p.get("name", p["id"])); rl.addWidget(cb)
            badge = QLabel(p.get("status", "wip"))
            badge.setStyleSheet(f'color:{BADGE.get(p.get("status","wip"),"#999")};font-size:10px')
            rl.addWidget(badge)
            note = QLabel(p.get("note", "")); note.setWordWrap(True); note.setStyleSheet("color:#888;font-size:10px")
            rl.addWidget(note)
            col.addWidget(row); self.boxes.append((p["id"], cb))
        col.addStretch(1)
        root = QVBoxLayout(self); root.addLayout(top); root.addWidget(scroll, 1)

    def _apply(self):
        self.on_build([pid for pid, cb in self.boxes if cb.isChecked()])
