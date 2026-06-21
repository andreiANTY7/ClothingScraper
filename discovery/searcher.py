from urllib.parse import urlparse
from duckduckgo_search import DDGS

_QUERIES = [
    "men's wholesale clothing B2B no brand",
    "angro haine barbati fara brand grossista",
    "wholesale streetwear men supplier Europe unbranded",
    "grossista abbigliamento uomo streetwear B2B",
    "toptan erkek giyim B2B wholesale",
]


def _extract_domain(url: str) -> str | None:
    try:
        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        pass
    return None


def search_candidate_sites(max_results: int = 5) -> list[str]:
    """Run DDG queries and return deduplicated domain base URLs."""
    domains: set[str] = set()
    with DDGS() as ddgs:
        for query in _QUERIES:
            try:
                results = ddgs.text(query, max_results=max_results)
                for r in results:
                    domain = _extract_domain(r.get("href", ""))
                    if domain:
                        domains.add(domain)
            except Exception:
                continue
    return list(domains)


def _domains_overlap(url_a: str, url_b: str) -> bool:
    """True if two URLs share the same effective domain (ignoring www prefix)."""
    a = urlparse(url_a).netloc.lstrip("www.").rstrip(".")
    b = urlparse(url_b).netloc.lstrip("www.").rstrip(".")
    if not a or not b:
        return False
    return a == b or a.endswith("." + b) or b.endswith("." + a)


def filter_known_sites(candidate_urls: list[str], known_urls: set[str]) -> list[str]:
    """Remove candidates whose domain overlaps with any known URL."""
    result = []
    for url in candidate_urls:
        if not any(_domains_overlap(url, known) for known in known_urls):
            result.append(url)
    return result
