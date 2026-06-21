import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from discovery.validator import validate_site, _find_product_links

pytestmark = pytest.mark.asyncio


@pytest.mark.asyncio
async def test_validate_site_returns_false_on_navigation_error(mocker):
    mock_page = mocker.AsyncMock()
    mock_page.goto.side_effect = Exception("Navigation timeout")
    mock_page.url = "https://example.com"

    mock_ctx = mocker.AsyncMock()
    mock_ctx.new_page.return_value = mock_page

    mock_browser = mocker.AsyncMock()
    mock_browser.new_context.return_value = mock_ctx

    mock_pw = mocker.AsyncMock()
    mock_pw.chromium.launch.return_value = mock_browser

    mock_apc = mocker.AsyncMock()
    mock_apc.__aenter__ = mocker.AsyncMock(return_value=mock_pw)
    mock_apc.__aexit__ = mocker.AsyncMock(return_value=False)
    mocker.patch("discovery.validator.async_playwright", return_value=mock_apc)

    result = await validate_site(
        "https://example.com", mocker.MagicMock(), [], [], 5.0
    )
    assert result["is_valid"] is False
    assert result["product_count"] == 0
    assert result["preview_products"] == []


@pytest.mark.asyncio
async def test_validate_site_detects_login_wall(mocker):
    mock_page = mocker.AsyncMock()
    mock_page.goto.return_value = None
    mock_page.url = "https://example.com/login"
    mock_page.content.return_value = "<html><body>Login required</body></html>"
    mock_page.eval_on_selector_all.return_value = []

    mock_ctx = mocker.AsyncMock()
    mock_ctx.new_page.return_value = mock_page

    mock_browser = mocker.AsyncMock()
    mock_browser.new_context.return_value = mock_ctx

    mock_pw = mocker.AsyncMock()
    mock_pw.chromium.launch.return_value = mock_browser

    mock_apc = mocker.AsyncMock()
    mock_apc.__aenter__ = mocker.AsyncMock(return_value=mock_pw)
    mock_apc.__aexit__ = mocker.AsyncMock(return_value=False)
    mocker.patch("discovery.validator.async_playwright", return_value=mock_apc)

    result = await validate_site(
        "https://example.com", mocker.MagicMock(), [], [], 5.0
    )
    assert result["requires_login"] is True


@pytest.mark.asyncio
async def test_validate_site_returns_preview_products(mocker):
    mock_page = mocker.AsyncMock()
    mock_page.goto.return_value = None
    mock_page.url = "https://example.com"
    mock_page.eval_on_selector_all.return_value = [
        "https://example.com/product/1",
        "https://example.com/product/2",
    ]
    mock_page.content.return_value = "<html><body>Product</body></html>"

    mock_ctx = mocker.AsyncMock()
    mock_ctx.new_page.return_value = mock_page

    mock_browser = mocker.AsyncMock()
    mock_browser.new_context.return_value = mock_ctx

    mock_pw = mocker.AsyncMock()
    mock_pw.chromium.launch.return_value = mock_browser

    mock_apc = mocker.AsyncMock()
    mock_apc.__aenter__ = mocker.AsyncMock(return_value=mock_pw)
    mock_apc.__aexit__ = mocker.AsyncMock(return_value=False)
    mocker.patch("discovery.validator.async_playwright", return_value=mock_apc)

    mocker.patch("discovery.validator.extract_product_from_html", return_value={
        "name": "Tricou Oversize",
        "price_eur": 8.5,
        "image_url": "https://example.com/img.jpg",
        "category": "t-shirts",
        "description": "cotton oversize",
        "is_men": True,
        "is_streetwear": True,
    })
    mocker.patch("discovery.validator.is_streetwear_men", return_value=True)

    result = await validate_site(
        "https://example.com", mocker.MagicMock(),
        ["t-shirt", "hoodie"], ["socks"], 5.0
    )
    assert result["is_valid"] is True
    assert result["product_count"] >= 1
    assert result["preview_products"][0]["name"] == "Tricou Oversize"
