import json, pathlib, pytest
import tbmosaic

DEC = pathlib.Path("decrypted")
MOSAICS = ["SuperNova.json", "BlitzinMatrix.json", "FlyingFloMatrix.json"]

def load(name): return json.load(open(DEC / name, encoding="utf-8"))

@pytest.mark.parametrize("name", MOSAICS)
def test_roundtrip_layers_identical(name):
    obj = load(name)
    before = {k: obj.get(k) for k in ("colors", "tags", "groups")}
    g = tbmosaic.from_obj(obj)
    tbmosaic.to_obj(g, obj)
    for k, v in before.items():
        assert obj.get(k) == v, k

def test_is_mosaic():
    assert tbmosaic.is_mosaic(load("SuperNova.json"))
    assert not tbmosaic.is_mosaic({"Coins": 0})

def test_edit_cell_roundtrips():
    obj = load("SuperNova.json")
    g = tbmosaic.from_obj(obj)
    g.cells[20][0].color = "R"      # was 'Y'
    g.cells[22][5].tag = "8"        # place a powerup
    tbmosaic.to_obj(g, obj)
    assert obj["colors"][20][0] == "R"
    assert obj["tags"][22][5] == "8"
    g2 = tbmosaic.from_obj(obj)
    assert g2.cells[20][0].color == "R" and g2.cells[22][5].tag == "8"

def test_color_palette():
    g = tbmosaic.from_obj(load("SuperNova.json"))
    pal = tbmosaic.color_palette(g)
    assert set(pal) == set("YLNBR")
    assert "." not in pal
