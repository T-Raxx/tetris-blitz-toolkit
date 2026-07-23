import json, pathlib

MOSAIC_FILES = {"SuperNova", "BlitzinMatrix", "FlyingFloMatrix"}
SYM_FILE = "mosaic_symbols.json"
_sym_cache = None

def symbols(layer, path=SYM_FILE):
    """RE'd char tables per mosaic layer: {char: {name, frame?}}. 'colors' | 'tags' | 'groups'."""
    global _sym_cache
    if _sym_cache is None:
        p = pathlib.Path(path)
        _sym_cache = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    return _sym_cache.get(layer, {})

class Cell:
    __slots__ = ("color", "tag", "group")
    def __init__(self, color=".", tag=".", group="."):
        self.color, self.tag, self.group = color, tag, group

class Grid:
    def __init__(self, rows, cols, cells, present):
        self.rows, self.cols, self.cells, self.present = rows, cols, cells, present

def is_mosaic(obj):
    c = obj.get("colors")
    return (isinstance(c, list) and len(c) > 0 and all(isinstance(r, str) for r in c)
            and len({len(r) for r in c}) == 1)

def _rows_of(obj, key, rows, cols):
    v = obj.get(key)
    if not (isinstance(v, list) and v and all(isinstance(r, str) for r in v)):
        return None
    return [(r + "." * cols)[:cols] for r in v] + ["." * cols] * (rows - len(v))

def from_obj(obj):
    colors = obj["colors"]
    rows, cols = len(colors), len(colors[0])
    present = {k for k in ("colors", "tags", "groups") if isinstance(obj.get(k), list)}
    layers = {k: (_rows_of(obj, k, rows, cols) or ["." * cols] * rows)
              for k in ("colors", "tags", "groups")}
    cells = [[Cell(layers["colors"][r][c], layers["tags"][r][c], layers["groups"][r][c])
              for c in range(cols)] for r in range(rows)]
    return Grid(rows, cols, cells, present)

def _layer_nonempty(grid, attr):
    return any(getattr(grid.cells[r][c], attr) != "." for r in range(grid.rows) for c in range(grid.cols))

def to_obj(grid, obj):
    def build(attr):
        return ["".join(getattr(grid.cells[r][c], attr) for c in range(grid.cols))
                for r in range(grid.rows)]
    obj["colors"] = build("color")
    for key, attr in (("tags", "tag"), ("groups", "group")):
        if key in grid.present or _layer_nonempty(grid, attr):
            obj[key] = build(attr)

def color_palette(grid):
    seen = []
    for r in range(grid.rows):
        for c in range(grid.cols):
            ch = grid.cells[r][c].color
            if ch != "." and ch not in seen:
                seen.append(ch)
    return seen
