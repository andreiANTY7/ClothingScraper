import sqlite3
import os

_SCHEMA = os.path.join(os.path.dirname(__file__), "schema.sql")


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
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


def insert_discovered_site(
    conn: sqlite3.Connection, url: str,
    product_count: int = 0, requires_login: bool = False
) -> int | None:
    cur = conn.execute(
        """INSERT OR IGNORE INTO discovered_sites (url, product_count, requires_login)
           VALUES (?, ?, ?)""",
        (url, product_count, int(requires_login)),
    )
    conn.commit()
    # If a row was actually inserted, cur.rowcount will be 1; otherwise it's 0
    if cur.rowcount > 0:
        return cur.lastrowid
    return None


def get_pending_discovered_sites(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM discovered_sites WHERE status = 'pending' ORDER BY discovered_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def get_approved_discovered_sites(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM discovered_sites WHERE status = 'approved' ORDER BY discovered_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def update_discovered_site_status(
    conn: sqlite3.Connection, site_id: int, status: str
) -> None:
    conn.execute(
        """UPDATE discovered_sites
           SET status = ?, reviewed_at = CURRENT_TIMESTAMP
           WHERE id = ?""",
        (status, site_id),
    )
    conn.commit()


def insert_preview_product(
    conn: sqlite3.Connection, site_url: str, product: dict
) -> None:
    conn.execute(
        """INSERT OR IGNORE INTO site_preview_products
           (site_url, name, image_url, price_eur, category, product_url)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (site_url, product.get("name"), product.get("image_url"),
         product.get("price_eur"), product.get("category"),
         product.get("product_url")),
    )
    conn.commit()


def get_preview_products(conn: sqlite3.Connection, site_url: str) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM site_preview_products WHERE site_url = ?",
        (site_url,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_all_known_urls(conn: sqlite3.Connection) -> set[str]:
    """Return base URLs of all sites ever processed (pending + reviewed)."""
    rows = conn.execute("SELECT url FROM discovered_sites").fetchall()
    return {r["url"] for r in rows}
