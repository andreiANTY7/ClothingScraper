import re
from collections import Counter

_STOP_WORDS = {
    "the", "a", "an", "and", "or", "of", "in", "for", "with",
    "to", "is", "it", "this", "that", "de", "cu", "si", "la", "pe"
}


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-ZÀ-ÿ]{3,}", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS]


def build_keyword_profile(liked_products: list[dict]) -> dict[str, int]:
    if not liked_products:
        return {}
    counter: Counter = Counter()
    for p in liked_products:
        text = " ".join([p.get("name", ""), p.get("description", ""), p.get("category", "")])
        counter.update(_tokenize(text))
    return dict(counter)


def score_product(product: dict, keyword_profile: dict[str, int]) -> float:
    if not keyword_profile:
        return 0.0
    text = " ".join([product.get("name", ""), product.get("description", ""), product.get("category", "")])
    tokens = set(_tokenize(text))
    total_weight = sum(keyword_profile.values())
    matched_weight = sum(keyword_profile.get(t, 0) for t in tokens)
    raw = matched_weight / total_weight if total_weight > 0 else 0.0
    return min(1.0, raw)


def rescore_all(conn, liked_products: list[dict]) -> None:
    """Re-score all products in DB using current liked set."""
    from db.db import get_all_products, update_product_score
    profile = build_keyword_profile(liked_products)
    for product in get_all_products(conn):
        score = score_product(product, profile)
        update_product_score(conn, product["id"], score)
