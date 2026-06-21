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
