import asyncio
from playwright.async_api import async_playwright
from anthropic import Anthropic

from scraper.generic import extract_product_from_html, is_streetwear_men

_PRODUCT_SELECTORS = [
    "a[href*='/product']",
    "a[href*='/products']",
    "a[href*='/item']",
    "a[href*='/catalog']",
    ".product-card a",
    ".product-item a",
    "a.product-link",
]


async def _find_product_links(page, base_url: str) -> list[str]:
    links: set[str] = set()
    for selector in _PRODUCT_SELECTORS:
        try:
            found = await page.eval_on_selector_all(
                selector, "els => els.map(e => e.href)"
            )
            links.update(found)
            if len(links) >= 5:
                break
        except Exception:
            continue
    return [link for link in links if link.startswith("http")][:5]


async def validate_site(
    base_url: str,
    anthropic_client: Anthropic,
    include_kw: list[str],
    exclude_kw: list[str],
    eur_ron: float,
) -> dict:
    """
    Visit a candidate site with headless Playwright, extract up to 3 product pages
    via the generic AI scraper, and return validation results.

    Returns:
        {
            "is_valid": bool,       # True if >=1 relevant product found
            "product_count": int,
            "preview_products": list[dict],
            "requires_login": bool,
        }
    """
    preview_products: list[dict] = []
    requires_login = False

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        try:
            try:
                await page.goto(base_url, timeout=20000, wait_until="domcontentloaded")
            except Exception:
                return {
                    "is_valid": False,
                    "product_count": 0,
                    "preview_products": [],
                    "requires_login": False,
                }

            if any(kw in page.url for kw in ["/login", "/signin", "/account"]):
                requires_login = True

            product_links = await _find_product_links(page, base_url)

            for link in product_links[:3]:
                try:
                    await page.goto(link, timeout=15000, wait_until="domcontentloaded")
                    html = await page.content()
                except Exception:
                    continue

                product = extract_product_from_html(html, link, anthropic_client)
                if product is None:
                    continue
                if not is_streetwear_men(product, include_kw, exclude_kw):
                    continue

                preview_products.append({
                    "name": product.get("name", ""),
                    "image_url": product.get("image_url"),
                    "price_eur": product.get("price_eur"),
                    "category": product.get("category"),
                    "product_url": link,
                })
        finally:
            await browser.close()

    return {
        "is_valid": len(preview_products) >= 1,
        "product_count": len(preview_products),
        "preview_products": preview_products,
        "requires_login": requires_login,
    }


def run_validate_site(
    base_url: str,
    anthropic_client: Anthropic,
    include_kw: list[str],
    exclude_kw: list[str],
    eur_ron: float,
) -> dict:
    """Sync wrapper for validate_site."""
    return asyncio.run(
        validate_site(base_url, anthropic_client, include_kw, exclude_kw, eur_ron)
    )
