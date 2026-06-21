import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# We need to stub streamlit imports before importing saved.py
import types
st_stub = types.ModuleType("streamlit")
sys.modules["streamlit"] = st_stub
import pandas as pd_real
sys.modules["pandas"] = pd_real

from ui.saved import _calc

CFG = {
    "transport_lei": 10,
    "packaging_lei": 7,
    "platform_fee_pct": 2.5,
    "ads_per_day_lei": 200,
    "partners": {"user": 0.40, "trex": 0.30, "partner2": 0.30},
}


def test_calc_basic():
    saved = {
        "price_lei": 40.0,
        "transport_lei": 10.0,
        "packaging_lei": 7.0,
        "platform_fee_pct": 2.5,
        "retail_price_lei": 130.0,
    }
    m = _calc(saved, CFG)
    # platform_fee = 130 * 0.025 = 3.25
    # total_cost = 40 + 10 + 7 + 3.25 = 60.25
    assert m["total_cost"] == 60.25
    # gross_margin = 130 - 60.25 = 69.75
    assert m["gross_margin"] == 69.75
    # net_8 = 69.75 - 200/8 = 69.75 - 25 = 44.75
    assert m["net_8"] == 44.75
    # user_8 = 44.75 * 0.40 = 17.9
    assert m["user_8"] == 17.9


def test_calc_zero_retail_gives_zero_margin():
    saved = {"price_lei": 40.0, "retail_price_lei": 0}
    m = _calc(saved, CFG)
    assert m["gross_margin_pct"] == 0
    assert m["breakeven_days"] is None


def test_calc_uses_cfg_defaults_when_saved_values_none():
    saved = {"price_lei": 40.0, "retail_price_lei": 130.0,
             "transport_lei": None, "packaging_lei": None, "platform_fee_pct": None}
    m = _calc(saved, CFG)
    # Should use cfg defaults: transport=10, packaging=7, fee=2.5%
    assert m["total_cost"] == 60.25
