import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scraper.generic import extract_product_from_html, is_streetwear_men


SAMPLE_HTML = """
<html><body>
<h1>Tricou Oversize Washed Black</h1>
<span class="price">8.50 EUR</span>
<img src="https://example.com/img.jpg" />
<p>100% cotton oversize fit, perfect for streetwear looks. Men's collection.</p>
</body></html>
"""

SAMPLE_RESPONSE = {
    "name": "Tricou Oversize Washed Black",
    "price_eur": 8.5,
    "image_url": "https://example.com/img.jpg",
    "category": "t-shirts",
    "description": "100% cotton oversize fit, perfect for streetwear looks. Men's collection.",
    "is_men": True,
    "is_streetwear": True,
}


def test_extract_product_calls_claude(mocker):
    mock_client = mocker.MagicMock()
    import json
    mock_client.messages.create.return_value.content[0].text = json.dumps(SAMPLE_RESPONSE)

    result = extract_product_from_html(SAMPLE_HTML, "https://example.com/p/1", mock_client)
    assert result is not None
    assert result["name"] == "Tricou Oversize Washed Black"
    assert result["price_eur"] == 8.5
    assert result["is_streetwear"] is True
    mock_client.messages.create.assert_called_once()


def test_extract_returns_none_on_invalid_json(mocker):
    mock_client = mocker.MagicMock()
    mock_client.messages.create.return_value.content[0].text = "not json at all"
    result = extract_product_from_html(SAMPLE_HTML, "https://example.com/p/1", mock_client)
    assert result is None


def test_is_streetwear_men_true():
    product = {"name": "Cargo Pants Men Streetwear", "category": "pants", "description": ""}
    assert is_streetwear_men(product, ["cargo", "pants", "streetwear"], ["socks", "underwear"]) is True


def test_is_streetwear_men_false_excluded_keyword():
    product = {"name": "Men Socks Pack", "category": "socks", "description": "cotton socks"}
    assert is_streetwear_men(product, ["t-shirt", "pants"], ["socks", "underwear"]) is False


def test_is_streetwear_men_false_no_match():
    product = {"name": "Formal Suit Jacket", "category": "suits", "description": "business formal"}
    assert is_streetwear_men(product, ["t-shirt", "hoodie", "cargo"], ["suit", "formal"]) is False
