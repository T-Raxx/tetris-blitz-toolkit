import tbmods

def test_unlock_everything_helpers_and_shop():
    helper = {"helpers": [
        {"uId": 1, "type": 0, "active": 2, "unlockedByDefault": False, "price": 6000, "promotion": True,
         "numFreePOWUses": 1, "typeId": 5},
        {"uId": 49, "type": 1, "active": 0, "unlockedByDefault": False, "price": 75000, "typeId": 10},
    ]}
    shop = {"products": [{"available": 0, "name": "A"}, {"available": 0, "name": "B"}]}
    tbmods.unlock_everything(helper, shop)
    for x in helper["helpers"]:
        assert x["active"] == 1 and x["unlockedByDefault"] is True and x["price"] == 0
        assert x["promotion"] is False
    assert helper["helpers"][0]["numFreePOWUses"] == 99
    assert all(p["available"] == 1 for p in shop["products"])

def test_apply_and_stage_unlock_everything(tmp_path):
    out = tbmods.apply_and_stage({"unlock_everything": True}, stage_dir=str(tmp_path))
    assert "unlock_everything" in out["applied"]
    assert "helper.json" in out["staged"] and "ShopItems.json" in out["staged"]
    import tbfiles, tbcrypt
    st = tmp_path / "assets" / "Assets" / "Coefficients"
    si = tbfiles.load_bytes((st / "ShopItems.json").read_bytes(), tbcrypt.load_key()).obj
    assert all(p["available"] == 1 for p in si["products"])           # every IAP shown
    h = tbfiles.load_bytes((st / "helper.json").read_bytes(), tbcrypt.load_key()).obj
    assert all(x["unlockedByDefault"] is True and x["price"] == 0 for x in h["helpers"])
