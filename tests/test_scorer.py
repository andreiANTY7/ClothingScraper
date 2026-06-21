import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from learning.scorer import build_keyword_profile, score_product


def make_product(name, description="", category=""):
    return {"name": name, "description": description, "category": category}


def test_build_profile_from_liked():
    liked = [
        make_product("Tricou Oversize Washed", "cotton streetwear oversize", "t-shirts"),
        make_product("Hoodie Basic Black", "fleece hoodie streetwear", "hoodies"),
    ]
    profile = build_keyword_profile(liked)
    assert profile.get("streetwear", 0) == 2
    assert profile.get("oversize", 0) == 2  # appears in name and description
    assert profile.get("hoodie", 0) >= 1


def test_empty_liked_returns_empty_profile():
    assert build_keyword_profile([]) == {}


def test_score_zero_with_no_profile():
    product = make_product("Cargo Pants", "utility cargo pockets")
    assert score_product(product, {}) == 0.0


def test_score_higher_for_matching_keywords():
    profile = {"oversize": 3, "streetwear": 2, "cotton": 1}
    product_match = make_product("Tricou Oversize", "cotton streetwear oversize tee")
    product_no_match = make_product("Formal Shirt", "dress shirt collar button")
    score_match = score_product(product_match, profile)
    score_no = score_product(product_no_match, profile)
    assert score_match > score_no


def test_score_clamped_0_to_1():
    profile = {"oversize": 100, "streetwear": 100}
    product = make_product("Oversize Streetwear Tee", "oversize streetwear oversize")
    s = score_product(product, profile)
    assert 0.0 <= s <= 1.0
