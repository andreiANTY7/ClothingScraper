import json
import re
from anthropic import Anthropic

_EXTRACT_PROMPT = """You are a product data extractor for a wholesale clothing B2B tool.
Extract product info from the HTML below and return ONLY valid JSON with these fields:
- name: string (product name)
- price_eur: number or null (price in EUR, convert if in other currency)
- image_url: string or null (main product image URL, absolute)
- category: string (one of: t-shirts, hoodies, pants, shorts, jackets, shirts, other)
- description: string (brief description, max 200 chars)
- is_men: boolean (is this a men's product?)
- is_streetwear: boolean (is this casual/streetwear style, not formal/underwear/socks?)

If you cannot extract a product (e.g. it's a category page, login wall, error page), return: {{"error": "not a product page"}}

URL: {url}

HTML (truncated):
{html}

Return ONLY the JSON object, no explanation."""


def _truncate_html(html: str, max_chars: int = 6000) -> str:
    """Remove script/style tags and truncate."""
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    html = re.sub(r"\s+", " ", html)
    return html[:max_chars]


def extract_product_from_html(html: str, url: str, client: Anthropic) -> dict | None:
    """Call Claude to extract product data from page HTML. Returns dict or None."""
    truncated = _truncate_html(html)
    prompt = _EXTRACT_PROMPT.format(url=url, html=truncated)
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        data = json.loads(raw)
        if "error" in data:
            return None
        return data
    except (json.JSONDecodeError, KeyError, IndexError):
        return None


def is_streetwear_men(product: dict, include_keywords: list[str], exclude_keywords: list[str]) -> bool:
    """Return True if product matches streetwear men's criteria."""
    text = " ".join([
        product.get("name", ""),
        product.get("category", ""),
        product.get("description", ""),
    ]).lower()
    for kw in exclude_keywords:
        if kw.lower() in text:
            return False
    for kw in include_keywords:
        if kw.lower() in text:
            return True
    return False
