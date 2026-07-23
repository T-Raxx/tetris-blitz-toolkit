import tbsounds

def test_list_sounds():
    s = tbsounds.list_sounds()
    assert len(s) > 200 and all(p.suffix == ".mp3" for p in s)

def test_detect_sounds_referenced_and_orphan():
    finds = {f["title"]: f for f in tbsounds.detect_sounds()}
    assert finds["BGM_RegularGameplayLoop"]["status"] == "referenced"      # registered in SoundBank
    assert finds["BGM_RegularGameplayLoop_Retro"]["status"] == "orphan"    # cut '_Retro' leftover
    for f in finds.values():
        assert f["category"] == "sound" and f["sound_path"].endswith(".mp3")
