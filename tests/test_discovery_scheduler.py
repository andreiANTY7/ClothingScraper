import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from discovery.scheduler import run_discovery
from scraper.runner import discovered_site_to_config
from db.db import init_db, get_pending_discovered_sites, get_preview_products


@pytest.fixture
def conn():
    c = init_db(":memory:")
    yield c
    c.close()


def test_run_discovery_inserts_valid_sites(conn, mocker):
    mocker.patch(
        "discovery.scheduler.search_candidate_sites",
        return_value=["https://new-b2b-site.com"],
    )
    mocker.patch(
        "discovery.scheduler.filter_known_sites",
        return_value=["https://new-b2b-site.com"],
    )
    mocker.patch("discovery.scheduler.get_all_known_urls", return_value=set())
    mocker.patch(
        "discovery.scheduler.run_validate_site",
        return_value={
            "is_valid": True,
            "product_count": 2,
            "preview_products": [
                {"name": "Tricou", "image_url": None, "price_eur": 9.0,
                 "category": "t-shirts", "product_url": "https://new-b2b-site.com/p/1"},
            ],
            "requires_login": False,
        },
    )

    cfg = {
        "anthropic_api_key": "test-key",
        "streetwear_include_keywords": ["t-shirt"],
        "streetwear_exclude_keywords": ["socks"],
        "eur_ron_rate": 5.0,
    }

    count = run_discovery(conn, cfg)
    assert count == 1
    pending = get_pending_discovered_sites(conn)
    assert len(pending) == 1
    assert pending[0]["url"] == "https://new-b2b-site.com"
    previews = get_preview_products(conn, "https://new-b2b-site.com")
    assert len(previews) == 1


def test_run_discovery_skips_invalid_sites(conn, mocker):
    mocker.patch(
        "discovery.scheduler.search_candidate_sites",
        return_value=["https://irrelevant-site.com"],
    )
    mocker.patch(
        "discovery.scheduler.filter_known_sites",
        return_value=["https://irrelevant-site.com"],
    )
    mocker.patch("discovery.scheduler.get_all_known_urls", return_value=set())
    mocker.patch(
        "discovery.scheduler.run_validate_site",
        return_value={
            "is_valid": False,
            "product_count": 0,
            "preview_products": [],
            "requires_login": False,
        },
    )

    cfg = {
        "anthropic_api_key": "test-key",
        "streetwear_include_keywords": ["t-shirt"],
        "streetwear_exclude_keywords": ["socks"],
        "eur_ron_rate": 5.0,
    }

    count = run_discovery(conn, cfg)
    assert count == 0
    assert len(get_pending_discovered_sites(conn)) == 0


def test_discovered_site_to_config_generates_valid_config():
    site = {"url": "https://www.example-b2b.com", "requires_login": 0}
    config = discovered_site_to_config(site)
    assert config["base_url"] == "https://www.example-b2b.com"
    assert config["men_listing_urls"] == ["https://www.example-b2b.com"]
    assert "product" in config["product_link_selector"].lower()
    assert config["requires_login"] is False
    assert isinstance(config["name"], str)
    assert len(config["name"]) > 0


def test_discovered_site_to_config_requires_login():
    site = {"url": "https://b2b-shop.net", "requires_login": 1}
    config = discovered_site_to_config(site)
    assert config["requires_login"] is True
