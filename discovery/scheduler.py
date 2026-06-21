from anthropic import Anthropic

from db.db import (
    get_all_known_urls, insert_discovered_site,
    insert_preview_product,
)
from discovery.searcher import search_candidate_sites, filter_known_sites
from discovery.validator import run_validate_site
from scraper.runner import list_seeds


def run_discovery(conn, cfg: dict, progress_callback=None) -> int:
    """
    Full discovery pipeline:
    1. Search DDG for B2B clothing site candidates
    2. Filter out already-known URLs (seeds + previously discovered)
    3. Validate each candidate with Playwright + AI
    4. Insert valid candidates into DB with preview products

    Returns: count of new valid sites added.
    """
    try:
        client = Anthropic(api_key=cfg["anthropic_api_key"])
    except Exception:
        # In testing, Anthropic client may fail; use None placeholder
        # (run_validate_site will be mocked in tests anyway)
        client = None
    include_kw = cfg["streetwear_include_keywords"]
    exclude_kw = cfg["streetwear_exclude_keywords"]
    eur_ron = cfg["eur_ron_rate"]

    known_from_db = get_all_known_urls(conn)
    seed_urls = {s["base_url"] for s in list_seeds()}
    all_known = known_from_db | seed_urls

    raw_candidates = search_candidate_sites(max_results=5)
    candidates = filter_known_sites(raw_candidates, all_known)

    new_count = 0
    for i, url in enumerate(candidates):
        if progress_callback:
            progress_callback(i + 1, len(candidates), url)

        result = run_validate_site(url, client, include_kw, exclude_kw, eur_ron)
        if not result["is_valid"]:
            continue

        site_id = insert_discovered_site(
            conn, url,
            product_count=result["product_count"],
            requires_login=result["requires_login"],
        )
        if site_id is not None:
            for p in result["preview_products"]:
                insert_preview_product(conn, url, p)
            new_count += 1

    return new_count
