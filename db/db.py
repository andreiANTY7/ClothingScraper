import sqlite3
import os

_SCHEMA = os.path.join(os.path.dirname(__file__), "schema.sql")


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    with open(_SCHEMA) as f:
        conn.executescript(f.read())
    conn.commit()
    return conn


def insert_product(conn: sqlite3.Connection, product: dict) -> int:
    cur = conn.execute(
        """INSERT OR IGNORE INTO products
           (site, url, name, image_url, price_eur, price_lei, category, description, score)
           VALUES (:site, :url, :name, :image_url, :price_eur, :price_lei, :category, :description, :score)""",
        product,
    )
    conn.commit()
    if cur.lastrowid:
        return cur.lastrowid
    row = conn.execute("SELECT id FROM products WHERE url = ?", (product["url"],)).fetchone()
    return row["id"]


def get_unseen_products(conn: sqlite3.Connection, limit: int = 100) -> list[dict]:
    rows = conn.execute(
        """SELECT p.* FROM products p
           WHERE p.id NOT IN (SELECT product_id FROM ratings)
           ORDER BY p.score DESC, p.scraped_at DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def rate_product(conn: sqlite3.Connection, product_id: int, rating: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO ratings (product_id, rating) VALUES (?, ?)",
        (product_id, rating),
    )
    conn.execute("UPDATE products SET seen = 1 WHERE id = ?", (product_id,))
    conn.commit()


def get_liked_products(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """SELECT p.* FROM products p
           JOIN ratings r ON r.product_id = p.id
           WHERE r.rating = 'like'""",
    ).fetchall()
    return [dict(r) for r in rows]


def save_product(conn: sqlite3.Connection, product_id: int) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO saved_products (product_id) VALUES (?)",
        (product_id,),
    )
    conn.commit()


def get_saved_products(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """SELECT sp.*, p.name, p.image_url, p.price_lei, p.price_eur,
                  p.site, p.url AS product_url, p.category, p.description
           FROM saved_products sp
           JOIN products p ON p.id = sp.product_id
           ORDER BY sp.saved_at DESC""",
    ).fetchall()
    return [dict(r) for r in rows]


def update_saved_product_pricing(
    conn: sqlite3.Connection,
    saved_id: int,
    retail_price_lei: float,
    transport_lei: float,
    packaging_lei: float,
    platform_fee_pct: float,
    notes: str = "",
) -> None:
    conn.execute(
        """UPDATE saved_products
           SET retail_price_lei = ?, transport_lei = ?, packaging_lei = ?,
               platform_fee_pct = ?, notes = ?
           WHERE id = ?""",
        (retail_price_lei, transport_lei, packaging_lei, platform_fee_pct, notes, saved_id),
    )
    conn.commit()


def update_product_score(conn: sqlite3.Connection, product_id: int, score: float) -> None:
    conn.execute("UPDATE products SET score = ? WHERE id = ?", (score, product_id))
    conn.commit()


def get_all_products(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM products ORDER BY score DESC").fetchall()
    return [dict(r) for r in rows]
