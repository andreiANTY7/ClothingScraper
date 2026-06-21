import pytest
import sqlite3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.db import init_db, insert_product, get_unseen_products, rate_product, \
    save_product, get_saved_products, update_product_score, get_liked_products, \
    update_saved_product_pricing


@pytest.fixture
def conn():
    c = init_db(":memory:")
    yield c
    c.close()


def sample_product(url="https://example.com/product/1"):
    return {
        "site": "btobturk",
        "url": url,
        "name": "Tricou Oversize Washed",
        "image_url": "https://example.com/img.jpg",
        "price_eur": 8.5,
        "price_lei": 42.5,
        "category": "t-shirts",
        "description": "100% cotton oversize fit streetwear",
        "score": 0.0,
    }


def test_insert_and_retrieve_product(conn):
    pid = insert_product(conn, sample_product())
    assert pid > 0
    rows = get_unseen_products(conn, limit=10)
    assert len(rows) == 1
    assert rows[0]["name"] == "Tricou Oversize Washed"


def test_duplicate_url_ignored(conn):
    insert_product(conn, sample_product())
    insert_product(conn, sample_product())  # same URL
    rows = get_unseen_products(conn, limit=10)
    assert len(rows) == 1


def test_rate_product_like(conn):
    pid = insert_product(conn, sample_product())
    rate_product(conn, pid, "like")
    liked = get_liked_products(conn)
    assert len(liked) == 1
    assert liked[0]["id"] == pid


def test_rate_product_dislike_not_in_liked(conn):
    pid = insert_product(conn, sample_product())
    rate_product(conn, pid, "dislike")
    liked = get_liked_products(conn)
    assert len(liked) == 0


def test_rated_product_not_in_unseen(conn):
    pid = insert_product(conn, sample_product())
    rate_product(conn, pid, "like")
    rows = get_unseen_products(conn)
    assert len(rows) == 0


def test_save_product(conn):
    pid = insert_product(conn, sample_product())
    save_product(conn, pid)
    saved = get_saved_products(conn)
    assert len(saved) == 1
    assert saved[0]["product_id"] == pid


def test_update_saved_pricing(conn):
    pid = insert_product(conn, sample_product())
    save_product(conn, pid)
    saved = get_saved_products(conn)
    spid = saved[0]["id"]
    update_saved_product_pricing(conn, spid, retail_price_lei=130.0, transport_lei=10.0,
                                  packaging_lei=7.0, platform_fee_pct=2.5)
    saved = get_saved_products(conn)
    assert saved[0]["retail_price_lei"] == 130.0


def test_update_product_score(conn):
    pid = insert_product(conn, sample_product())
    update_product_score(conn, pid, 0.85)
    rows = get_unseen_products(conn)
    assert rows[0]["score"] == 0.85
