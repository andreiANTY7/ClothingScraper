import streamlit as st
from pathlib import Path
from db.db import init_db

st.set_page_config(
    page_title="Brand Scraper",
    page_icon="🧢",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = Path(__file__).parent / "brand_scraper.db"


@st.cache_resource
def get_db():
    return init_db(str(DB_PATH))


conn = get_db()

page = st.sidebar.radio(
    "Navigare",
    ["🔍 Browse", "⭐ Salvate & Prețuri", "⚙️ Setări"],
    label_visibility="collapsed",
)

st.sidebar.divider()
from db.db import get_unseen_products, get_saved_products
unseen = get_unseen_products(conn, limit=1000)
saved = get_saved_products(conn)
st.sidebar.metric("Produse de revăzut", len(unseen))
st.sidebar.metric("Produse salvate", len(saved))

if page == "🔍 Browse":
    from ui.browse import render
    render(conn)
elif page == "⭐ Salvate & Prețuri":
    from ui.saved import render
    render(conn)
elif page == "⚙️ Setări":
    from ui.settings import render
    render(conn)
