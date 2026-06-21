CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    image_url TEXT,
    price_eur REAL,
    price_lei REAL,
    category TEXT,
    description TEXT,
    score REAL DEFAULT 0.0,
    seen INTEGER DEFAULT 0,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER UNIQUE NOT NULL REFERENCES products(id),
    rating TEXT NOT NULL CHECK(rating IN ('like','dislike','skip')),
    rated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS saved_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER UNIQUE NOT NULL REFERENCES products(id),
    transport_lei REAL DEFAULT 10.0,
    packaging_lei REAL DEFAULT 7.0,
    platform_fee_pct REAL DEFAULT 2.5,
    retail_price_lei REAL,
    notes TEXT,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS discovered_sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK(status IN ('pending','approved','rejected','blacklisted')),
    product_count INTEGER DEFAULT 0,
    requires_login INTEGER DEFAULT 0,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS site_preview_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_url TEXT NOT NULL,
    name TEXT,
    image_url TEXT,
    price_eur REAL,
    category TEXT,
    product_url TEXT UNIQUE,
    FOREIGN KEY(site_url) REFERENCES discovered_sites(url)
);
