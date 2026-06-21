import streamlit as st
import asyncio
import json
from pathlib import Path
from anthropic import Anthropic

from db.db import get_unseen_products, rate_product, save_product, get_liked_products
from learning.scorer import rescore_all
from scraper.runner import scrape_site, list_seeds
from scraper.session_manager import has_session

CONFIG_PATH = Path(__file__).parent.parent / "config.json"


def _cfg() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def render(conn) -> None:
    st.title("Browse Produse")

    cfg = _cfg()
    col_scrape, col_info = st.columns([2, 3])

    with col_scrape:
        st.subheader("Scrape site nou")
        from db.db import get_approved_discovered_sites
        from scraper.runner import discovered_site_to_config
        approved_discovered = get_approved_discovered_sites(conn)
        seeds = list_seeds() + [discovered_site_to_config(s) for s in approved_discovered]
        site_names = [s["display_name"] for s in seeds]
        chosen_display = st.selectbox("Site", site_names)
        chosen_seed = next(s for s in seeds if s["display_name"] == chosen_display)

        needs_login = chosen_seed.get("requires_login", True)
        has_sess = has_session(chosen_seed["name"])

        if needs_login and not has_sess:
            st.warning("Mergi la Setări și autentifică-te mai întâi.")
        else:
            if st.button("▶ Start Scraping"):
                client = Anthropic(api_key=cfg["anthropic_api_key"])
                progress_text = st.empty()
                counter = st.empty()

                def on_progress(count, url):
                    progress_text.caption(f"Procesez: {url[:60]}...")
                    counter.metric("Produse găsite", count)

                count = asyncio.run(scrape_site(
                    chosen_seed, conn, client,
                    cfg["streetwear_include_keywords"],
                    cfg["streetwear_exclude_keywords"],
                    cfg["eur_ron_rate"],
                    progress_callback=on_progress,
                ))
                rescore_all(conn, get_liked_products(conn))
                st.success(f"Gata! {count} produse noi adăugate.")
                st.rerun()

    products = get_unseen_products(conn, limit=200)

    if not products:
        st.info("Nu mai sunt produse de revăzut. Rulează un scraping sau adaugă un site nou.")
        return

    st.divider()
    col_list, col_detail = st.columns([2, 3])

    if "selected_idx" not in st.session_state:
        st.session_state.selected_idx = 0

    with col_list:
        st.caption(f"Produse de revăzut: {len(products)}")
        for i, p in enumerate(products):
            score_badge = f"🟢 {p['score']:.0%}" if p["score"] > 0.5 else f"⚪ {p['score']:.0%}"
            label = f"{p['name'][:35]}{'...' if len(p['name']) > 35 else ''}"
            price_str = f"{p['price_lei']:.0f} lei" if p.get("price_lei") else f"{p.get('price_eur', '?')} EUR"
            btn_label = f"{label}\n{p['site']} · {price_str} · {score_badge}"
            if st.button(btn_label, key=f"sel_{i}", use_container_width=True):
                st.session_state.selected_idx = i

    with col_detail:
        idx = min(st.session_state.selected_idx, len(products) - 1)
        p = products[idx]

        if p.get("image_url"):
            st.image(p["image_url"], use_column_width=True)

        st.subheader(p["name"])
        price_str = f"{p['price_lei']:.0f} lei (~{p.get('price_eur', '?')} EUR)"
        st.markdown(f"**{p['site']}** · {price_str} · _{p.get('category', '')}_")
        if p.get("description"):
            st.caption(p["description"])
        if p.get("url"):
            st.markdown(f"[🔗 Vezi pe site]({p['url']})")

        st.divider()
        col_like, col_save, col_skip, col_dis = st.columns(4)
        pid = p["id"]

        if col_like.button("👍 Like", key=f"like_{pid}", use_container_width=True):
            rate_product(conn, pid, "like")
            rescore_all(conn, get_liked_products(conn))
            st.rerun()

        if col_save.button("⭐ Salvează", key=f"save_{pid}", use_container_width=True):
            rate_product(conn, pid, "like")
            save_product(conn, pid)
            rescore_all(conn, get_liked_products(conn))
            st.success("Salvat în lista de prețuri!")
            st.rerun()

        if col_skip.button("⏭ Skip", key=f"skip_{pid}", use_container_width=True):
            rate_product(conn, pid, "skip")
            st.rerun()

        if col_dis.button("👎 Dislike", key=f"dis_{pid}", use_container_width=True):
            rate_product(conn, pid, "dislike")
            rescore_all(conn, get_liked_products(conn))
            st.rerun()
