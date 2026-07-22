from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QGridLayout, QLabel,
    QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, QComboBox, QScrollArea)
import tbmods

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
        lay.addWidget(self.pu_pick)
        row = QHBoxLayout()
        for preset in ("clear_whole_matrix", "max_perks", "free_unlock"):
            b = QPushButton(preset); b.clicked.connect(lambda _, pr=preset: self._add_behavior(preset=pr))
            row.addWidget(b)
        lay.addLayout(row)
        self.param_box = QGroupBox("raw params (numeric)"); self.param_box.setLayout(QGridLayout())
        lay.addWidget(self.param_box)
        addraw = QPushButton("Add raw params"); addraw.clicked.connect(lambda: self._add_behavior(raw=True))
        lay.addWidget(addraw)
        self.behavior_lbl = QLabel("no behavior mods queued"); lay.addWidget(self.behavior_lbl)
        self._param_widgets = {}
        self._rebuild_params()
        return g

    def _rebuild_params(self, *_):
        grid = self.param_box.layout()
        while grid.count():
            w = grid.takeAt(0).widget()
            if w: w.deleteLater()
        self._param_widgets = {}
        p = self._pu_by_label.get(self.pu_pick.currentText()) or {}
        r = 0
        for k, v in (p.get("params") or {}).items():
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                continue
            b = QDoubleSpinBox() if isinstance(v, float) else _intbox()
            b.setRange(-INT_MAX, INT_MAX); b.setValue(v)
            self._param_widgets[k] = b
            grid.addWidget(QLabel(k), r, 0); grid.addWidget(b, r, 1); r += 1

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

    def _build_config(self):
        cur = {"on": self.cur_on.isChecked()}
        keymap = {"Coins": "coins", "PremiumCoins": "premium", "PremiumShards": "shards",
                  "GrindShards": "shards", "SkillShards": "shards", "Spins": "spins"}
        for name in CUR_FIELDS:
            cur[keymap[name]] = self.cur_fields[name].value()
        cur["level"] = self.cur_level.value() or None
        cur["xp"] = self.cur_xp.value() or None
        return {"currency": cur, "unlock_all": self.unlock_all.isChecked(),
                "show_hidden": self.show_hidden.isChecked(), "all_free": self.all_free.isChecked(),
                "behavior": list(self.behavior),
                "coin_awards": {"on": self.coin_on.isChecked(), "multiplier": self.coin_mult.value()},
                "rename_flonase": self.rename_flonase.isChecked()}

    def _apply(self):
        self.on_build(self._build_config())
