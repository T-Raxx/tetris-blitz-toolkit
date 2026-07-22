from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QGridLayout, QLabel,
    QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, QComboBox, QScrollArea)
from PyQt6.QtGui import QPixmap
import pathlib
import tbmods, tbsemantics, tbassets

INT_MAX = 2000000000
CUR_FIELDS = ["Coins", "PremiumCoins", "PremiumShards", "GrindShards", "SkillShards", "Spins"]

def _intbox(maximum=INT_MAX):
    b = QSpinBox(); b.setRange(-INT_MAX, INT_MAX); b.setMaximumWidth(160); return b

class ModBuilderTab(QWidget):
    def __init__(self, key, on_build):
        super().__init__()
        self.key, self.on_build = key, on_build
        self.behavior = []
        outer = QVBoxLayout(); root = QWidget(); root.setLayout(outer)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(root)
        QVBoxLayout(self).addWidget(scroll)

        outer.addWidget(self._currency_group())
        outer.addWidget(self._globals_group())
        outer.addWidget(self._behavior_group())
        outer.addWidget(self._coin_group())
        outer.addWidget(self._core_group())
        applyb = QPushButton("Apply + Build & Install APK"); applyb.clicked.connect(self._apply)
        outer.addWidget(applyb); outer.addStretch(1)

    def _currency_group(self):
        g = QGroupBox("Currency & Progression"); grid = QGridLayout(g)
        self.cur_on = QCheckBox("enable"); grid.addWidget(self.cur_on, 0, 0)
        self.cur_fields = {}
        for i, name in enumerate(CUR_FIELDS):
            b = _intbox(); self.cur_fields[name] = b
            mx = QPushButton("MAX"); mx.clicked.connect(lambda _, x=b: x.setValue(INT_MAX))
            grid.addWidget(QLabel(name), i + 1, 0); grid.addWidget(b, i + 1, 1); grid.addWidget(mx, i + 1, 2)
        self.cur_level = _intbox(); self.cur_xp = _intbox()
        grid.addWidget(QLabel("Level"), len(CUR_FIELDS) + 1, 0); grid.addWidget(self.cur_level, len(CUR_FIELDS) + 1, 1)
        grid.addWidget(QLabel("XP"), len(CUR_FIELDS) + 2, 0); grid.addWidget(self.cur_xp, len(CUR_FIELDS) + 2, 1)
        return g

    def _globals_group(self):
        g = QGroupBox("Powerups — global"); lay = QVBoxLayout(g)
        self.unlock_all = QCheckBox("Unlock all powerups")
        self.show_hidden = QCheckBox("Show hidden powerups (+ level fix)")
        self.all_free = QCheckBox("All powerups free")
        self.rename_flonase = QCheckBox('Rename Flonase → "(CRASHES GAME)"')
        for c in (self.unlock_all, self.show_hidden, self.all_free, self.rename_flonase):
            lay.addWidget(c)
        return g

    def _behavior_group(self):
        g = QGroupBox("Powerup behavior"); lay = QVBoxLayout(g)
        self.pu_pick = QComboBox(); self._pu_by_label = {}
        for p in tbmods.POWERUPS(self.key):
            label = f'{p["uId"]}: {p.get("iconBasePath","")}'
            self.pu_pick.addItem(label); self._pu_by_label[label] = p
        self.pu_pick.currentTextChanged.connect(self._rebuild_params)
        head = QHBoxLayout()
        self.pu_icon = QLabel(); self.pu_icon.setFixedSize(64, 64)
        head.addWidget(self.pu_icon); head.addWidget(self.pu_pick); head.addStretch(1)
        lay.addLayout(head)
        row = QHBoxLayout()
        for preset in ("clear_whole_matrix", "max_perks", "free_unlock"):
            b = QPushButton(preset); b.clicked.connect(lambda _, pr=preset: self._add_behavior(preset=pr))
            row.addWidget(b)
        lay.addLayout(row)
        self.param_box = QGroupBox("raw params (numeric)"); self.param_box.setLayout(QGridLayout())
        pscroll = QScrollArea(); pscroll.setWidgetResizable(True); pscroll.setWidget(self.param_box)
        pscroll.setMinimumHeight(120); pscroll.setMaximumHeight(220)
        lay.addWidget(pscroll)
        addraw = QPushButton("Add raw params"); addraw.clicked.connect(lambda: self._add_behavior(raw=True))
        lay.addWidget(addraw)
        self.behavior_lbl = QLabel("no behavior mods queued"); lay.addWidget(self.behavior_lbl)
        self._param_widgets = {}
        self._rebuild_params()
        return g

    def _set_icon(self, base):
        self.pu_icon.clear()
        if not base:
            return
        try:
            cache = pathlib.Path("build") / "iconcache"
            got = tbassets.extract_named(str(cache), [f"Common/{base}.png"])
            path = got.get(f"Common/{base}.png")
            if path:
                self.pu_icon.setPixmap(QPixmap(path).scaled(64, 64))
        except Exception:
            pass

    def _rebuild_params(self, *_):
        grid = self.param_box.layout()
        while grid.count():
            w = grid.takeAt(0).widget()
            if w: w.deleteLater()
        self._param_widgets = {}
        p = self._pu_by_label.get(self.pu_pick.currentText()) or {}
        pu_key = p.get("iconBasePath")
        r = 0
        for k, v in (p.get("params") or {}).items():
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                continue
            b = QDoubleSpinBox() if isinstance(v, float) else _intbox()
            b.setRange(-INT_MAX, INT_MAX); b.setValue(v)
            self._param_widgets[k] = b
            d = tbsemantics.describe(k, pu_key)
            lab = QLabel(d["label"] + (f'  [{d["hint"]}]' if d["hint"] else ""))
            lab.setToolTip(d["tooltip"]); b.setToolTip(d["tooltip"])
            grid.addWidget(lab, r, 0); grid.addWidget(b, r, 1); r += 1
        self._set_icon(pu_key)

    def _add_behavior(self, preset=None, raw=False):
        p = self._pu_by_label.get(self.pu_pick.currentText())
        if not p:
            return
        entry = {"uId": p["uId"]}
        if preset:
            entry["preset"] = preset
        if raw:
            entry["params"] = {k: w.value() for k, w in self._param_widgets.items()}
        self.behavior.append(entry)
        self.behavior_lbl.setText(f"{len(self.behavior)} queued: " +
            ", ".join(str(b.get("preset") or list(b.get("params", {}).keys())) for b in self.behavior))

    def _coin_group(self):
        g = QGroupBox("Coin awards"); grid = QGridLayout(g)
        self.coin_on = QCheckBox("enable"); grid.addWidget(self.coin_on, 0, 0)
        self.coin_mult = QDoubleSpinBox(); self.coin_mult.setRange(1, 1000); self.coin_mult.setValue(10)
        grid.addWidget(QLabel("multiplier"), 1, 0); grid.addWidget(self.coin_mult, 1, 1)
        return g

    def _core_values(self):
        try:
            return tbmods._load("CoreMechanicsCoefficients.json", self.key).obj
        except Exception:
            return {}

    def _core_group(self):
        g = QGroupBox("CoreMechanics quick-cheats"); grid = QGridLayout(g)
        self.core_on = QCheckBox("enable"); grid.addWidget(self.core_on, 0, 0, 1, 2)
        cur = self._core_values()
        self.core_fields = {}
        for i, c in enumerate(tbsemantics.CORE_CHEATS):
            b = _intbox(); b.setValue(int(cur.get(c["key"], 0) or 0))
            b.setToolTip(c["note"] or c["key"])
            self.core_fields[c["key"]] = b
            lab = QLabel(c["label"]); lab.setToolTip(c["key"])
            grid.addWidget(lab, i + 1, 0); grid.addWidget(b, i + 1, 1)
        return g

    def _build_config(self):
        cur = {"on": self.cur_on.isChecked()}
        keymap = {"Coins": "coins", "PremiumCoins": "premium", "PremiumShards": "shards",
                  "GrindShards": "shards", "SkillShards": "shards", "Spins": "spins"}
        for name in CUR_FIELDS:
            cur[keymap[name]] = self.cur_fields[name].value()
        cur["level"] = self.cur_level.value() or None
        cur["xp"] = self.cur_xp.value() or None
        core = {}
        if self.core_on.isChecked():
            for k, b in self.core_fields.items():
                core[k] = b.value()
        return {"currency": cur, "unlock_all": self.unlock_all.isChecked(),
                "show_hidden": self.show_hidden.isChecked(), "all_free": self.all_free.isChecked(),
                "behavior": list(self.behavior),
                "coin_awards": {"on": self.coin_on.isChecked(), "multiplier": self.coin_mult.value()},
                "core_mechanics": core,
                "rename_flonase": self.rename_flonase.isChecked()}

    def _apply(self):
        self.on_build(self._build_config())
