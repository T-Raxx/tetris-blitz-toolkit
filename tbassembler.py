from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QComboBox, QScrollArea, QGroupBox, QLineEdit)
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QIcon
from PyQt6.QtCore import Qt, QRect, QSize
import tbmosaic, tbassets

CELL = 18            # px per cell in the editable canvas
CACHE = "assets_cache"
LAYER_KEY = {"color": "colors", "tag": "tags", "group": "groups"}

def block_qcolor(ch):
    rgb = tbassets.color_swatch_map().get(ch)
    return QColor(*rgb) if rgb else QColor(90, 90, 90)

class Canvas(QWidget):
    def __init__(self, owner):
        super().__init__(); self.owner = owner
        g = owner.grid
        self.setFixedSize(g.cols * CELL + 1, g.rows * CELL + 1)

    def _cell_at(self, pos):
        c, r = pos.x() // CELL, pos.y() // CELL
        g = self.owner.grid
        return (r, c) if 0 <= r < g.rows and 0 <= c < g.cols else (None, None)

    def mousePressEvent(self, e): self._paint(e)
    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.MouseButton.LeftButton: self._paint(e)

    def _paint(self, e):
        r, c = self._cell_at(e.position().toPoint())
        if r is not None:
            self.owner.paint_cell(r, c); self.update()

    def paintEvent(self, _):
        p = QPainter(self); g = self.owner.grid
        for r in range(g.rows):
            for c in range(g.cols):
                cell = g.cells[r][c]; rect = QRect(c * CELL, r * CELL, CELL, CELL)
                if cell.color != ".":
                    px = self.owner.block_px.get(cell.color)
                    if px and not px.isNull(): p.drawPixmap(rect, px)   # real sprite
                    else: p.fillRect(rect, block_qcolor(cell.color))    # swatch fallback
                p.setPen(QPen(QColor(45, 47, 57))); p.drawRect(rect)
                if cell.tag != ".":
                    ic = self.owner.pu_px.get(cell.tag)
                    if ic and not ic.isNull(): p.drawPixmap(rect, ic)   # powerup icon
                    else:
                        p.setPen(QPen(QColor(255, 255, 255)))
                        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, cell.tag)

class Assembler(QWidget):
    def __init__(self, tbfile, on_change, name=None):
        super().__init__()
        self.tb, self.on_change = tbfile, on_change
        self.name = name                                   # source filename/stem -> finisher palette
        self.finisher = tbmosaic.finisher_name(name)
        self.grid = tbmosaic.from_obj(tbfile.obj)
        self.layer = "color"
        self.brush = (tbmosaic.color_palette(self.grid) or ["Y"])[0]
        self.block_px, self.pu_px = {}, {}
        self._load_sprites()

        self.canvas = Canvas(self)
        canvas_scroll = QScrollArea(); canvas_scroll.setWidget(self.canvas)

        self.layer_pick = QComboBox(); self.layer_pick.addItems(["color", "tag", "group"])
        self.layer_pick.currentTextChanged.connect(self._set_layer)

        self.palette_box = QGroupBox("Brush"); self.palette_box.setLayout(QVBoxLayout())
        self._build_palette()

        self.preview = QLabel(); self.preview.setMinimumWidth(220)
        self._render_preview()

        pal_scroll = QScrollArea(); pal_scroll.setWidgetResizable(True)
        pal_scroll.setWidget(self.palette_box); pal_scroll.setMinimumWidth(210)
        left = QVBoxLayout()
        left.addWidget(QLabel("Layer")); left.addWidget(self.layer_pick)
        left.addWidget(pal_scroll, 1)
        root = QHBoxLayout(self)
        root.addLayout(left); root.addWidget(canvas_scroll, 1)
        rightcol = QVBoxLayout()
        rightcol.addWidget(QLabel("Preview")); rightcol.addWidget(self.preview); rightcol.addStretch(1)
        root.addLayout(rightcol)

    def _load_sprites(self):
        # Real game sprites; any failure (no Pillow / no atlas) -> empty maps -> swatch fallback.
        try:
            for ch, p in tbassets.block_sprite_map(CACHE).items(): self.block_px[ch] = QPixmap(p)
            for ch, p in tbassets.tag_sprite_map(CACHE).items(): self.pu_px[ch] = QPixmap(p)
        except Exception:
            pass

    def _set_layer(self, name):
        self.layer = name; self._build_palette()

    def _build_palette(self):
        lay = self.palette_box.layout()
        while lay.count():
            w = lay.takeAt(0).widget()
            if w: w.deleteLater()
        layer_key = LAYER_KEY[self.layer]
        syms = tbmosaic.symbols(layer_key)                       # full RE'd symbol set for this layer
        pxmap = self.block_px if self.layer == "color" else self.pu_px
        own = set(tbmosaic.finisher_palette(self.finisher, layer_key)) if self.finisher else set()
        ordered = tbmosaic.palette_for(self.name, self.grid, layer_key)

        title = f"{self.finisher} palette" if self.finisher else "All minos"
        hdr = QLabel(title); hdr.setStyleSheet("color:#8fd18f;font-weight:bold")
        lay.addWidget(hdr)

        for txt, warn in self._layer_notes(layer_key):
            n = QLabel(txt); n.setWordWrap(True)
            n.setStyleSheet("color:%s;font-size:10px" % ("#e0a35a" if warn else "#9aa"))
            lay.addWidget(n)

        def add_btn(ch):
            meta = syms.get(ch, {})
            name = meta.get("name", ch); conf = meta.get("conf")
            star = "" if conf in (None, "confirmed") else ("*" if conf == "inferred" else "†")
            b = QPushButton(f"{ch}  {name}{star}")
            px = pxmap.get(ch)
            if px and not px.isNull():
                b.setIcon(QIcon(px)); b.setIconSize(QSize(18, 18))
            elif self.layer == "color":                          # colored chip fallback
                chip = QPixmap(18, 18); chip.fill(block_qcolor(ch))
                b.setIcon(QIcon(chip)); b.setIconSize(QSize(18, 18))
            tip = name
            if conf == "inferred": tip += "  (inferred — verify in-app)"
            if meta.get("note"): tip += f"\n{meta['note']}"
            b.setToolTip(tip)
            b.clicked.connect(lambda _, v=ch: setattr(self, "brush", v))
            lay.addWidget(b)

        shown = []
        for ch in ordered:                                       # finisher-own chars first
            if not own or ch in own:
                add_btn(ch); shown.append(ch)
        rest = [ch for ch in ordered if ch not in shown]
        if rest:
            sep = QLabel("— all minos —"); sep.setStyleSheet("color:#888;font-size:10px")
            lay.addWidget(sep)
            for ch in rest:
                add_btn(ch); shown.append(ch)

        er = QPushButton("erase (.)"); er.clicked.connect(lambda: setattr(self, "brush", "."))
        lay.addWidget(er)
        # free single-char brush (groups, or any custom char the game may accept)
        le = QLineEdit(); le.setMaxLength(1); le.setPlaceholderText("custom char")
        le.textChanged.connect(lambda t: setattr(self, "brush", t or "."))
        lay.addWidget(le)
        self.brush = (shown or [self.brush if self.brush != "." else "."])[0]

    def _layer_notes(self, layer_key):
        """Explanatory / warning notes shown above the brush palette. (text, is_warning)."""
        if layer_key != "tags":
            return []
        notes = [("Tags = powerups que el finisher OTORGA en su cinemática (fin de ronda), "
                  "NO tiles del tablero. Se ven en HUD/inventario al disparar el finisher y "
                  "requieren 'Unlock everything'. p/s = minos Progressive decorativos (no powerups).", False)]
        if self.finisher:
            has_pw = set(tbmosaic.finisher_palette(self.finisher, "tags")) & set("123456789ABC")
            if not has_pw:
                notes.append((f"⚠ {self.finisher} no usa tags de powerup (matriz cosmética) — "
                              "editar la capa tag no otorgará nada in-game.", True))
        return notes

    def paint_cell(self, r, c):
        cell = self.grid.cells[r][c]
        setattr(cell, self.layer, self.brush)
        tbmosaic.to_obj(self.grid, self.tb.obj)
        self._render_preview()
        self.on_change()

    def _render_preview(self):
        g = self.grid; scale = 6
        pm = QPixmap(g.cols * scale, g.rows * scale); pm.fill(QColor(20, 21, 28))
        p = QPainter(pm)
        for r in range(g.rows):
            for c in range(g.cols):
                ch = g.cells[r][c].color
                if ch == ".": continue
                rect = QRect(c * scale, r * scale, scale, scale)
                px = self.block_px.get(ch)
                if px and not px.isNull(): p.drawPixmap(rect, px)
                else: p.fillRect(rect, block_qcolor(ch))
        p.end()
        self.preview.setPixmap(pm)
