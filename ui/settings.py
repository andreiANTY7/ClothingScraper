import os
import streamlit as st
from scraper.session_manager import has_session, run_login
from scraper.runner import list_seeds
from utils.config import load_config, save_config

_IS_CLOUD = os.path.exists("/mount/src")


def render(conn) -> None:
    st.title("Setări")

    cfg = load_config()

    st.subheader("API & Curs valutar")
    api_key = st.text_input("Anthropic API Key", value=cfg.get("anthropic_api_key", ""), type="password")
    eur_ron = st.number_input("Curs EUR/RON", value=float(cfg.get("eur_ron_rate", 5.0)), step=0.1)

    st.subheader("Costuri default per produs")
    col1, col2, col3 = st.columns(3)
    transport = col1.number_input("Transport (lei/buc)", value=float(cfg.get("transport_lei", 10)))
    packaging = col2.number_input("Packaging (lei/buc)", value=float(cfg.get("packaging_lei", 7)))
    platform_fee = col3.number_input("Shopify fee (%)", value=float(cfg.get("platform_fee_pct", 2.5)))

    st.subheader("Ads & Parteneri")
    ads = st.number_input("Buget ads/zi (lei)", value=float(cfg.get("ads_per_day_lei", 200)))
    partners = cfg.get("partners", {"user": 0.4, "trex": 0.3, "partner2": 0.3})
    col1, col2, col3 = st.columns(3)
    p_user = col1.number_input("Tu (%)", value=float(partners["user"] * 100), min_value=0.0, max_value=100.0)
    p_trex = col2.number_input("TREX (%)", value=float(partners["trex"] * 100), min_value=0.0, max_value=100.0)
    p2 = col3.number_input("Partener 2 (%)", value=float(partners["partner2"] * 100), min_value=0.0, max_value=100.0)

    if st.button("Salvează setările"):
        cfg.update({
            "anthropic_api_key": api_key,
            "eur_ron_rate": eur_ron,
            "transport_lei": transport,
            "packaging_lei": packaging,
            "platform_fee_pct": platform_fee,
            "ads_per_day_lei": ads,
            "partners": {"user": p_user / 100, "trex": p_trex / 100, "partner2": p2 / 100},
        })
        save_config(cfg)
        st.success("Salvat!")

    st.divider()
    st.subheader("Site-uri B2B — Autentificare")
    if _IS_CLOUD:
        st.info("🌐 Login-ul cu browser nu funcționează pe cloud. Rulează aplicația local pentru a salva sesiuni B2B.")
        return

    seeds = list_seeds()
    from db.db import get_approved_discovered_sites
    from scraper.runner import discovered_site_to_config
    approved_discovered = get_approved_discovered_sites(conn)
    discovered_configs = [discovered_site_to_config(s) for s in approved_discovered
                          if s.get("requires_login")]
    all_site_configs = seeds + discovered_configs

    for seed in all_site_configs:
        name = seed["name"]
        display = seed["display_name"]
        logged_in = has_session(name)
        login_url = seed.get("login_url", "")
        col1, col2, col3 = st.columns([3, 1, 1])
        col1.markdown(f"**{display}** — {'✅ Sesiune activă' if logged_in else '❌ Neautentificat'}")
        login_url = col2.text_input("Login URL", value=login_url, key=f"lurl_{name}", label_visibility="collapsed")
        if col3.button("Login", key=f"login_{name}"):
            with st.spinner(f"Deschid browserul pentru {display}..."):
                run_login(name, login_url)
            st.rerun()
