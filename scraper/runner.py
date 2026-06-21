import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
from anthropic import Anthropic

from scraper.generic import extract_product_from_html, is_streetwear_men
from scraper.session_manager import get_authenticated_context
from db.db import insert_product

SEEDS_DIR = Path(__file__).parent / "seeds"


def load_seed(site_name: str) -> dict:
    return json.loads((SEEDS_DIR / f"{site_name}.json").read_text())


def list_seeds() -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(SEEDS_DIR.glob("*.json"))]


async def scrape_site(site_config: dict, conn, anthropic_client: Anthropic,
                      include_kw: list[str], exclude_kw: list[str],
                      eur_ron: float, progress_callback=None) -> int:
    """Scrape a site and insert matching products into DB. Returns count inserted."""
    site_name = site_config["name"]
    inserted = 0

    async with async_playwright() as p:
        ctx = await get_authenticated_context(site_name, p)
        if ctx is None:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context()

        page = await ctx.new_page()

        for listing_url in site_config["men_listing_urls"]:
            try:
                await page.goto(listing_url, timeout=30000, wait_until="networkidle")
            except Exception:
                continue

            try:
                links = await page.eval_on_selector_all(
                    site_config["product_link_selector"],
                    "els => els.map(e => e.href)"
                )
            except Exception:
                continue

            links = list(set(links))[:50]

            for link in links:
                if not link.startswith("http"):
                    continue
                try:
                    await page.goto(link, timeout=20000, wait_until="domcontentloaded")
                    html = await page.content()
                except Exception:
                    continue

                product = extract_product_from_html(html, link, anthropic_client)
                if product is None:
                    continue
                if not is_streetwear_men(product, include_kw, exclude_kw):
                    continue

                row = {
                    "site": site_name,
                    "url": link,
                    "name": product.get("name", "Unknown"),
                    "image_url": product.get("image_url"),
                    "price_eur": product.get("price_eur"),
                    "price_lei": (product.get("price_eur") or 0) * eur_ron,
                    "category": product.get("category", "other"),
                    "description": product.get("description", ""),
                    "score": 0.0,
                }
                insert_product(conn, row)
                inserted += 1
                if progress_callback:
                    progress_callback(inserted, link)

        await ctx.close()

    return inserted
