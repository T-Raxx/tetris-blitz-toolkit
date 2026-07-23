import tbsounds

def test_list_sounds():
    s = tbsounds.list_sounds()
    assert len(s) > 200 and all(p.suffix == ".mp3" for p in s)

def test_detect_sounds_referenced_and_orphan():
    finds = {f["title"]: f for f in tbsounds.detect_sounds()}
    assert finds["BGM_RegularGameplayLoop"]["status"] == "referenced"
    assert finds["SFX_FLN_MinoPlacement_01"]["status"] == "orphan"
    for f in finds.values():
        assert f["category"] == "sound" and f["sound_path"].endswith(".mp3")
