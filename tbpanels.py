from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QSpinBox, QPushButton, QGroupBox,
    QGridLayout, QTableWidget, QTableWidgetItem, QScrollArea)

SAVE_CURRENCY = ["Coins","PremiumCoins","PremiumShards","GrindShards","SkillShards",
                 "Spins","GoldRushGames","Energy"]
KNOWN_COEFF = ["EnergyRefilTimeSec","DefaultMaxEnergy","NumberOfCoinsForPushNotificationEnable"]
INT_MAX = 2000000000

def coeff_quick_fields(obj):
    out = [k for k in obj if isinstance(k, str) and k.startswith("NumberOfCoinsFor")
           and isinstance(obj[k], int)]
    out += [k for k in KNOWN_COEFF if isinstance(obj.get(k), int) and k not in out]
    return out

def _intbox(val):
    b = QSpinBox(); b.setRange(-INT_MAX, INT_MAX); b.setValue(int(val)); b.setMaximumWidth(180)
    return b

def build_smart(tb, on_change):
    root = QWidget(); outer = QVBoxLayout(root)
    if tb.fmt == "save":
        outer.addWidget(_currency_group(tb, on_change))
        outer.addWidget(_progression_group(tb, on_change))
        outer.addWidget(_powerups_group(tb, on_change))
    else:
        fields = coeff_quick_fields(tb.obj)
        if fields:
            outer.addWidget(_coeff_group(tb, fields, on_change))
        else:
            outer.addWidget(QLabel("No quick-cheat fields in this file — use the Raw JSON tab."))
    outer.addStretch(1)
    scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(root)
    return scroll

def _currency_group(tb, on_change):
    g = QGroupBox("Currency"); grid = QGridLayout(g)
    row = 0
    for key in SAVE_CURRENCY:
        if key not in tb.obj: continue
        box = _intbox(tb.obj[key])
        box.valueChanged.connect(lambda v, k=key: (tb.obj.__setitem__(k, int(v)), on_change()))
        mx = QPushButton("MAX")
        mx.clicked.connect(lambda _, b=box: b.setValue(INT_MAX))
        grid.addWidget(QLabel(key), row, 0); grid.addWidget(box, row, 1); grid.addWidget(mx, row, 2)
        row += 1
    return g

def _progression_group(tb, on_change):
    g = QGroupBox("Progression"); grid = QGridLayout(g)
    ld = tb.obj.get("LevelData", {})
    if "Level" in ld:
        box = _intbox(ld["Level"])
        box.valueChanged.connect(lambda v: (ld.__setitem__("Level", int(v)), on_change()))
        grid.addWidget(QLabel("Level"), 0, 0); grid.addWidget(box, 0, 1)
    if "XP" in tb.obj:
        xb = _intbox(tb.obj["XP"])
        xb.valueChanged.connect(lambda v: (tb.obj.__setitem__("XP", int(v)), on_change()))
        grid.addWidget(QLabel("XP"), 1, 0); grid.addWidget(xb, 1, 1)
    return g

def _powerups_group(tb, on_change):
    g = QGroupBox("Powerup Inventory (Id / Quantity / Level)"); lay = QVBoxLayout(g)
    inv = tb.obj.get("HelperInventory", [])
    tbl = QTableWidget(len(inv), 3)
    tbl.setHorizontalHeaderLabels(["Id","Quantity","Level"])
    for r, item in enumerate(inv):
        for c, k in enumerate(("Id","Quantity","Level")):
            tbl.setItem(r, c, QTableWidgetItem(str(item.get(k, 0))))
    def commit(*_):
        for r, item in enumerate(inv):
            for c, k in enumerate(("Id","Quantity","Level")):
                cell = tbl.item(r, c)
                if cell:
                    try: item[k] = int(cell.text())
                    except ValueError: pass
        on_change()
    tbl.cellChanged.connect(commit)
    lay.addWidget(tbl)
    return g

def _coeff_group(tb, fields, on_change):
    g = QGroupBox("Quick Cheats"); grid = QGridLayout(g)
    for i, key in enumerate(fields):
        box = _intbox(tb.obj[key])
        box.valueChanged.connect(lambda v, k=key: (tb.obj.__setitem__(k, int(v)), on_change()))
        grid.addWidget(QLabel(key), i, 0); grid.addWidget(box, i, 1)
    return g
