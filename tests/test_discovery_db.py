import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.db import (
    init_db, insert_discovered_site, get_pending_discovered_sites,
    get_approved_discovered_sites, update_discovered_site_status,
    insert_preview_product, get_preview_products, get_all_known_urls,
)


@pytest.fixture
def conn():
    c = init_db(":memory:")
    yield c
    c.close()


def test_insert_discovered_site(conn):
    site_id = insert_discovered_site(conn, "https://example.com", product_count=3)
    assert site_id is not None
    pending = get_pending_discovered_sites(conn)
    assert len(pending) == 1
    assert pending[0]["url"] == "https://example.com"
    assert pending[0]["product_count"] == 3
    assert pending[0]["status"] == "pending"


def test_insert_duplicate_site_returns_none(conn):
    insert_discovered_site(conn, "https://example.com", product_count=3)
    result = insert_discovered_site(conn, "https://example.com", product_count=5)
    assert result is None
    assert len(get_pending_discovered_sites(conn)) == 1


def test_update_status_to_approved(conn):
    site_id = insert_discovered_site(conn, "https://example.com")
    update_discovered_site_status(conn, site_id, "approved")
    pending = get_pending_discovered_sites(conn)
    approved = get_approved_discovered_sites(conn)
    assert len(pending) == 0
    assert len(approved) == 1


def test_update_status_to_rejected(conn):
    site_id = insert_discovered_site(conn, "https://example.com")
    update_discovered_site_status(conn, site_id, "rejected")
    assert len(get_pending_discovered_sites(conn)) == 0
    assert len(get_approved_discovered_sites(conn)) == 0


def test_insert_and_get_preview_products(conn):
    insert_discovered_site(conn, "https://example.com")
    insert_preview_product(conn, "https://example.com", {
        "name": "Tricou Oversize",
        "image_url": "https://example.com/img.jpg",
        "price_eur": 8.5,
        "category": "t-shirts",
        "product_url": "https://example.com/product/1",
    })
    previews = get_preview_products(conn, "https://example.com")
    assert len(previews) == 1
    assert previews[0]["name"] == "Tricou Oversize"
    assert previews[0]["price_eur"] == 8.5


def test_insert_duplicate_preview_product_ignored(conn):
    insert_discovered_site(conn, "https://example.com")
    p = {"name": "Tricou", "image_url": None, "price_eur": 9.0,
         "category": "t-shirts", "product_url": "https://example.com/p/1"}
    insert_preview_product(conn, "https://example.com", p)
    insert_preview_product(conn, "https://example.com", p)
    assert len(get_preview_products(conn, "https://example.com")) == 1


def test_get_all_known_urls(conn):
    insert_discovered_site(conn, "https://site-a.com")
    insert_discovered_site(conn, "https://site-b.com")
    update_discovered_site_status(conn,
        get_pending_discovered_sites(conn)[0]["id"], "approved")
    known = get_all_known_urls(conn)
    assert "https://site-a.com" in known
    assert "https://site-b.com" in known
