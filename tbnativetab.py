from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton,
    QScrollArea, QFrame, QSpinBox)
import tbnative

BADGE = {"works": "#8fd18f", "wip": "#d9b45a", "crashes": "#e06767"}

def pct_to_pace(pct, lo, hi):
    pct = max(1, int(pct))
    return max(lo, min(hi, round(100 / pct)))

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
        self.boxes = []; self.param_ctrls = {}; self._param_meta = {}
        for p in self.patches:
            row = QFrame(); row.setFrameShape(QFrame.Shape.StyledPanel); rl = QVBoxLayout(row)
            cb = QCheckBox(p.get("name", p["id"])); rl.addWidget(cb)
            badge = QLabel(p.get("status", "wip"))
            badge.setStyleSheet(f'color:{BADGE.get(p.get("status","wip"),"#999")};font-size:10px')
            rl.addWidget(badge)
            note = QLabel(p.get("note", "")); note.setWordWrap(True); note.setStyleSheet("color:#888;font-size:10px")
            rl.addWidget(note)
            prm = p.get("param")
            if prm:
                lo, hi = prm.get("min", 1), prm.get("max", 50)
                pr = QHBoxLayout(); sb = QSpinBox(); sb.setRange(1, 100)
                sb.setValue(max(1, round(100 / prm.get("default", 3))))
                info = QLabel(""); info.setStyleSheet("color:#8fd18f;font-size:10px")
                def _upd(v, lo=lo, hi=hi, info=info):
                    n = pct_to_pace(v, lo, hi); info.setText(f"1 powerup every {n} pieces (~{round(100/n)}%/piece)")
                sb.valueChanged.connect(_upd); _upd(sb.value())
                pr.addWidget(QLabel("chance %/piece")); pr.addWidget(sb); pr.addWidget(info); pr.addStretch(1)
                rl.addLayout(pr)
                self.param_ctrls[p["id"]] = sb; self._param_meta[p["id"]] = (prm["name"], lo, hi)
            col.addWidget(row); self.boxes.append((p["id"], cb))
        col.addStretch(1)
        root = QVBoxLayout(self); root.addLayout(top); root.addWidget(scroll, 1)

    def _apply(self):
        ids = [pid for pid, cb in self.boxes if cb.isChecked()]
        values = {}
        for pid in ids:
            if pid in self.param_ctrls:
                name, lo, hi = self._param_meta[pid]
                values[pid] = {name: pct_to_pace(self.param_ctrls[pid].value(), lo, hi)}
        self.on_build(ids, values)
