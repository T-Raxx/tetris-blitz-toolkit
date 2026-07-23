from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QSpinBox,
    QCheckBox, QPushButton, QFileDialog, QMessageBox)
import tbsave, tbadb

class SaveTab(QWidget):
    """Samsung save as patch base: load genuine PlayerData+NarcSave, apply coherent mods, export/push."""
    def __init__(self, key):
        super().__init__()
        self.key = key
        self.base = None
        root = QVBoxLayout(self)
        root.addWidget(QLabel("Save base (Samsung)"))
        note = QLabel("Parte de tu save real (evento desbloqueado, Level grandfathered). NarcSave se "
                      "preserva. Level/XP NO editable (el juego lo recomputa — pendiente confirmar). "
                      "Push requiere adb (rooted/dev); non-rooted usa el APK builder.")
        note.setWordWrap(True); note.setStyleSheet("color:#9aa;font-size:11px")
        root.addWidget(note)

        self.status = QLabel("—"); self.status.setStyleSheet("color:#8fd18f")
        root.addWidget(self.status)

        grid = QGridLayout()
        self.spins = {}
        for i, field in enumerate(["Coins", "PremiumCoins", "PremiumShards", "GrindShards",
                                   "SkillShards", "Spins", "GoldRushGames", "Energy"]):
            sb = QSpinBox(); sb.setRange(0, tbsave.MAXINT); sb.setGroupSeparatorShown(True)
            grid.addWidget(QLabel(field), i // 2, (i % 2) * 2)
            grid.addWidget(sb, i // 2, (i % 2) * 2 + 1)
            self.spins[field] = sb
        root.addLayout(grid)

        self.unlock_all = QCheckBox("Unlock all content in save (agrega uIds faltantes a Unlocks[])")
        self.max_help = QCheckBox("Max all helpers (Level 5, owned)")
        root.addWidget(self.unlock_all); root.addWidget(self.max_help)

        row = QHBoxLayout()
        maxb = QPushButton("MAX currency"); maxb.clicked.connect(self._max_currency)
        reloadb = QPushButton("Reload base"); reloadb.clicked.connect(self._load)
        exportb = QPushButton("Export modded save → folder"); exportb.clicked.connect(self._export)
        pushb = QPushButton("Push to device"); pushb.clicked.connect(self._push)
        for b in (reloadb, maxb, exportb, pushb):
            row.addWidget(b)
        root.addLayout(row); root.addStretch(1)
        self._load()

    def _load(self):
        try:
            self.base = tbsave.load_base(key=self.key)
            pd = tbsave.playerdata(self.base); s = tbsave.summary(pd)
            for f, sb in self.spins.items():
                sb.setValue(min(int(pd.get(f, 0) or 0), tbsave.MAXINT))
            self.status.setText(f"base: Coins={s['coins']:,} Level={s['level']} XP={s['xp']} "
                                f"Unlocks={s['unlocks']} Helpers={s['helpers']}")
        except Exception as e:
            self.base = None; self.status.setText(f"no base: {e}")

    def _max_currency(self):
        for sb in self.spins.values():
            sb.setValue(tbsave.MAXINT)

    def _mods(self):
        return {"currency": {f: sb.value() for f, sb in self.spins.items()},
                "unlock_all": self.unlock_all.isChecked(),
                "max_helpers": self.max_help.isChecked()}

    def _fresh_modded(self):
        base = tbsave.load_base(key=self.key)              # fresh, so mods don't stack
        tbsave.apply_mods(base, self._mods(), key=self.key)
        return base

    def _export(self):
        if not self.base:
            return
        d = QFileDialog.getExistingDirectory(self, "Export modded save to folder")
        if not d:
            return
        try:
            written = tbsave.stage_modded(self._fresh_modded(), d, key=self.key)
        except Exception as e:
            QMessageBox.warning(self, "Export failed", str(e)); return
        QMessageBox.information(self, "Exported", f"{len(written)} file(s) → {d}")

    def _push(self):
        if not self.base:
            return
        try:
            dev = tbadb.device()
        except Exception:
            dev = None
        if not dev:
            QMessageBox.warning(self, "Push", "No adb device. Non-rooted → usa el APK builder."); return
        if QMessageBox.question(self, "Push save", f"Push modded PlayerData+NarcSave to {dev}?\n"
                                "(device save auto-backed up first)") != QMessageBox.StandardButton.Yes:
            return
        try:
            res = tbsave.push_to_device(self._fresh_modded(), key=self.key)
        except Exception as e:
            QMessageBox.warning(self, "Push failed", str(e)); return
        QMessageBox.information(self, "Pushed", f"pushed {res['pushed']}\nbackups {res['backups']}\n"
                               "Restart game to load.")
