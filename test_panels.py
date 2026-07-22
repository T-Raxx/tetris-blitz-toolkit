import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import tbpanels

def test_coeff_quick_fields_filters_present_keys():
    obj = {"NumberOfCoinsForFacebookLogin": 40000, "EnergyRefilTimeSec": 600, "Other": 1}
    fields = tbpanels.coeff_quick_fields(obj)
    assert "NumberOfCoinsForFacebookLogin" in fields
    assert "EnergyRefilTimeSec" in fields
    assert "Other" not in fields

def test_save_currency_list_stable():
    assert tbpanels.SAVE_CURRENCY[0] == "Coins"
    assert "PremiumCoins" in tbpanels.SAVE_CURRENCY
