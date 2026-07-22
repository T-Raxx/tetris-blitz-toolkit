from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QComboBox, QScrollArea, QGroupBox)
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap
from PyQt6.QtCore import Qt, QRect
import tbmosaic, tbassets

CELL = 18            # px per cell in the editable canvas
CACHE = "assets_cache"

def block_qcolor(ch):
    rgb = tbassets.LETTER_COLOR.get(ch)
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
    def __init__(self, tbfile, on_change):
        super().__init__()
        self.tb, self.on_change = tbfile, on_change
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

        left = QVBoxLayout()
        left.addWidget(QLabel("Layer")); left.addWidget(self.layer_pick)
        left.addWidget(self.palette_box); left.addStretch(1)
        root = QHBoxLayout(self)
        root.addLayout(left); root.addWidget(canvas_scroll, 1)
        rightcol = QVBoxLayout()
        rightcol.addWidget(QLabel("Preview")); rightcol.addWidget(self.preview); rightcol.addStretch(1)
        root.addLayout(rightcol)

    def _load_sprites(self):
        # Real game sprites; any failure (no Pillow / no atlas) -> empty maps -> swatch fallback.
        try:
            for ch, p in tbassets.block_sprite_map(CACHE).items(): self.block_px[ch] = QPixmap(p)
            for ch, p in tbassets.powerup_icon_map(CACHE).items(): self.pu_px[ch] = QPixmap(p)
        except Exception:
            pass

    def _set_layer(self, name):
        self.layer = name; self._build_palette()

    def _build_palette(self):
        lay = self.palette_box.layout()
        while lay.count():
            w = lay.takeAt(0).widget()
            if w: w.deleteLater()
        if self.layer == "color":
            opts = tbmosaic.color_palette(self.grid) or list("YLNBR")
            labels = {ch: ch for ch in opts}
        elif self.layer == "tag":
            opts = list(tbassets.POWERUP_NAME.keys())
            labels = {ch: f"{ch}  {tbassets.POWERUP_NAME[ch]}" for ch in opts}
        else:
            opts = []; labels = {}
        for ch in opts + ["."]:
            b = QPushButton(labels.get(ch, "erase (.)"))
            b.clicked.connect(lambda _, v=ch: setattr(self, "brush", v))
            lay.addWidget(b)
        if opts:
            self.brush = opts[0]

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
