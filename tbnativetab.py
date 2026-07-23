from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QPushButton,
    QScrollArea, QFrame, QSpinBox)
import tbnative

BADGE = {"works": "#8fd18f", "wip": "#d9b45a", "crashes": "#e06767"}

def pct_to_pace(pct, lo, hi):
    pct = max(1, int(pct))
    return max(lo, min(hi, round(100 / pct)))

def fps_to_ms(fps, uncapped):
    return 0 if uncapped else max(1, round(1000 / max(1, int(fps))))

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
        self.boxes = []; self.param_ctrls = {}; self._param_get = {}
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
                rl.addLayout(self._param_row(p["id"], prm))
            col.addWidget(row); self.boxes.append((p["id"], cb))
        col.addStretch(1)
        root = QVBoxLayout(self); root.addLayout(top); root.addWidget(scroll, 1)

    def _param_row(self, pid, prm):
        pr = QHBoxLayout(); info = QLabel(""); info.setStyleSheet("color:#8fd18f;font-size:10px")
        convert = prm.get("convert", "pct_to_pace")
        if convert == "fps_to_ms":
            lo, hi = prm.get("min", 30), prm.get("max", 240)
            sb = QSpinBox(); sb.setRange(lo, hi); sb.setValue(prm.get("default", 60))
            unc = QCheckBox("uncapped")
            def _upd(*_, sb=sb, unc=unc, info=info):
                if unc.isChecked(): info.setText("uncapped (0 ms/frame)")
                else: info.setText(f"{sb.value()} fps → {fps_to_ms(sb.value(), False)} ms/frame")
            sb.valueChanged.connect(_upd); unc.stateChanged.connect(_upd); _upd()
            pr.addWidget(QLabel("target fps")); pr.addWidget(sb); pr.addWidget(unc)
            getter = (lambda sb=sb, unc=unc: fps_to_ms(sb.value(), unc.isChecked()))
        else:  # pct_to_pace
            lo, hi = prm.get("min", 1), prm.get("max", 50)
            sb = QSpinBox(); sb.setRange(1, 100); sb.setValue(max(1, round(100 / prm.get("default", 3))))
            def _upd(*_, sb=sb, lo=lo, hi=hi, info=info):
                n = pct_to_pace(sb.value(), lo, hi); info.setText(f"1 powerup every {n} pieces (~{round(100/n)}%/piece)")
            sb.valueChanged.connect(_upd); _upd()
            pr.addWidget(QLabel("chance %/piece")); pr.addWidget(sb)
            getter = (lambda sb=sb, lo=lo, hi=hi: pct_to_pace(sb.value(), lo, hi))
        pr.addWidget(info); pr.addStretch(1)
        self.param_ctrls[pid] = sb                 # primary control (back-compat)
        self._param_get[pid] = (prm["name"], getter)
        return pr

    def selection(self):
        ids = [pid for pid, cb in self.boxes if cb.isChecked()]
        values = {}
        for pid in ids:
            if pid in self._param_get:
                name, getter = self._param_get[pid]
                values[pid] = {name: getter()}
        return ids, values

    def _apply(self):
        ids, values = self.selection()
        self.on_build(ids, values)
