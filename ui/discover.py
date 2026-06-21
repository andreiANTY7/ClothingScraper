import streamlit as st
from anthropic import Anthropic

from db.db import (
    get_pending_discovered_sites, update_discovered_site_status,
    get_preview_products, insert_discovered_site, insert_preview_product,
)
from discovery.scheduler import run_discovery
from discovery.validator import run_validate_site
from utils.config import load_config as _cfg


def render(conn) -> None:
    st.title("Descoperire Site-uri Noi")
    cfg = _cfg()

    # ── Manual add ──────────────────────────────────────────────────────────
    st.subheader("Adaugă site manual")
    col_url, col_btn = st.columns([4, 1])
    manual_url = col_url.text_input(
        "URL",
        placeholder="https://example-wholesale.com",
        label_visibility="collapsed",
        key="manual_url_input",
    )
    if col_btn.button("Validează", use_container_width=True) and manual_url.strip():
        url = manual_url.strip()
        with st.spinner(f"Validez {url}..."):
            client = Anthropic(api_key=cfg["anthropic_api_key"])
            result = run_validate_site(
                url, client,
                cfg["streetwear_include_keywords"],
                cfg["streetwear_exclude_keywords"],
                cfg["eur_ron_rate"],
            )
        if result["is_valid"]:
            site_id = insert_discovered_site(
                conn, url,
                product_count=result["product_count"],
                requires_login=result["requires_login"],
            )
            if site_id is not None:
                for p in result["preview_products"]:
                    insert_preview_product(conn, url, p)
            st.success(
                f"Site valid! {result['product_count']} produse găsite. "
                "Apare mai jos pentru aprobare."
            )
            st.rerun()
        else:
            st.error("Niciun produs relevant de streetwear bărbați găsit pe acest site.")

    st.divider()

    # ── Auto-discovery trigger ───────────────────────────────────────────────
    col1, col2 = st.columns([3, 1])
    col1.markdown(
        "**Căutare automată** — caută site-uri B2B noi pe web folosind DuckDuckGo"
    )
    if col2.button("🔍 Caută acum", use_container_width=True):
        progress_text = st.empty()

        def on_progress(current, total, url):
            progress_text.caption(f"Validez {current}/{total}: {url[:55]}...")

        with st.spinner("Caut și validez site-uri noi..."):
            count = run_discovery(conn, cfg, progress_callback=on_progress)
        progress_text.empty()

        if count > 0:
            st.success(f"{count} site-uri noi găsite! Apar mai jos.")
            st.rerun()
        else:
            st.info("Niciun site nou relevant găsit în această rundă.")

    st.divider()

    # ── Pending queue ────────────────────────────────────────────────────────
    st.subheader("Site-uri în așteptare")
    pending = get_pending_discovered_sites(conn)

    if not pending:
        st.info(
            "Niciun site nou în coadă. "
            "Apasă '🔍 Caută acum' sau adaugă manual un URL de mai sus."
        )
        return

    for site in pending:
        with st.expander(
            f"🌐 {site['url']} — {site['product_count']} produs(e) găsite"
            + (" 🔐" if site.get("requires_login") else ""),
            expanded=True,
        ):
            previews = get_preview_products(conn, site["url"])
            if previews:
                cols = st.columns(min(3, len(previews)))
                for i, p in enumerate(previews[:3]):
                    with cols[i]:
                        if p.get("image_url"):
                            st.image(p["image_url"], width=110)
                        st.caption(f"**{p.get('name', '—')}**")
                        price = (
                            f"{p['price_eur']:.2f} EUR"
                            if p.get("price_eur")
                            else "Preț necunoscut"
                        )
                        st.caption(price)

            col_a, col_r, col_b = st.columns(3)
            if col_a.button(
                "✅ Aprobă", key=f"approve_{site['id']}", use_container_width=True
            ):
                update_discovered_site_status(conn, site["id"], "approved")
                st.success(
                    "Aprobat! Site-ul apare acum în Browse → dropdown site-uri."
                )
                st.rerun()

            if col_r.button(
                "❌ Respinge", key=f"reject_{site['id']}", use_container_width=True
            ):
                update_discovered_site_status(conn, site["id"], "rejected")
                st.rerun()

            if col_b.button(
                "🚫 Niciodată", key=f"block_{site['id']}", use_container_width=True
            ):
                update_discovered_site_status(conn, site["id"], "blacklisted")
                st.rerun()
