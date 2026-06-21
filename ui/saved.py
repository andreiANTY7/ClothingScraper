import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

from db.db import get_saved_products, update_saved_product_pricing
from utils.config import load_config as _cfg

EXPORTS_DIR = Path(__file__).parent.parent / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)


def _calc(saved: dict, cfg: dict) -> dict:
    """Compute all financial metrics for one saved product."""
    cost = (saved.get("price_lei") or 0)
    transport = saved.get("transport_lei") or cfg["transport_lei"]
    packaging = saved.get("packaging_lei") or cfg["packaging_lei"]
    fee_pct = (saved.get("platform_fee_pct") or cfg["platform_fee_pct"]) / 100
    retail = saved.get("retail_price_lei") or 0
    partners = cfg["partners"]
    ads = cfg["ads_per_day_lei"]

    platform_fee_lei = retail * fee_pct
    total_cost = cost + transport + packaging + platform_fee_lei
    gross_margin = retail - total_cost

    def net_at(sales_per_day):
        if sales_per_day == 0:
            return 0.0
        ads_per_item = ads / sales_per_day
        return gross_margin - ads_per_item

    net_5 = net_at(5)
    net_8 = net_at(8)
    net_12 = net_at(12)

    return {
        "total_cost": round(total_cost, 2),
        "platform_fee_lei": round(platform_fee_lei, 2),
        "gross_margin": round(gross_margin, 2),
        "gross_margin_pct": round((gross_margin / retail * 100) if retail else 0, 1),
        "net_5": round(net_5, 2),
        "net_8": round(net_8, 2),
        "net_12": round(net_12, 2),
        "user_8": round(net_8 * partners["user"], 2),
        "trex_8": round(net_8 * partners["trex"], 2),
        "partner2_8": round(net_8 * partners["partner2"], 2),
        "breakeven_days": round(10000 / (net_8 * 8), 1) if net_8 > 0 else None,
    }


def _build_excel(saved_list: list[dict], cfg: dict) -> bytes:
    rows = []
    for s in saved_list:
        m = _calc(s, cfg)
        rows.append({
            "Produs": s["name"],
            "Site": s["site"],
            "Link": s.get("product_url", ""),
            "Cost marfă (lei)": s.get("price_lei", 0),
            "Transport (lei)": s.get("transport_lei") or cfg["transport_lei"],
            "Packaging (lei)": s.get("packaging_lei") or cfg["packaging_lei"],
            "Shopify fee (lei)": m["platform_fee_lei"],
            "Total cost (lei)": m["total_cost"],
            "Preț vânzare (lei)": s.get("retail_price_lei") or 0,
            "Marjă brută (lei)": m["gross_margin"],
            "Marjă brută (%)": m["gross_margin_pct"],
            "Profit net/buc 5 vânz/zi": m["net_5"],
            "Profit net/buc 8 vânz/zi": m["net_8"],
            "Profit net/buc 12 vânz/zi": m["net_12"],
            f"Tu ({int(cfg['partners']['user']*100)}%) la 8/zi": m["user_8"],
            f"TREX ({int(cfg['partners']['trex']*100)}%) la 8/zi": m["trex_8"],
            f"Partener ({int(cfg['partners']['partner2']*100)}%) la 8/zi": m["partner2_8"],
            "Break-even (zile, la 8/zi)": m["breakeven_days"],
        })
    df = pd.DataFrame(rows)
    path = EXPORTS_DIR / f"brand_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df.to_excel(path, index=False)
    return path.read_bytes()


def render(conn) -> None:
    st.title("Produse Salvate & Calculator Prețuri")
    cfg = _cfg()
    saved_list = get_saved_products(conn)

    if not saved_list:
        st.info("Niciun produs salvat încă. Mergi la Browse și apasă ⭐ Salvează.")
        return

    col_list, col_calc = st.columns([2, 3])

    if "saved_idx" not in st.session_state:
        st.session_state.saved_idx = 0

    with col_list:
        st.caption(f"{len(saved_list)} produse salvate")
        for i, s in enumerate(saved_list):
            price_str = f"{s['price_lei']:.0f} lei" if s.get("price_lei") else "?"
            retail_str = f"→ {s['retail_price_lei']:.0f} lei" if s.get("retail_price_lei") else "→ preț nesetat"
            label = f"{s['name'][:30]}\n{s['site']} · {price_str} {retail_str}"
            if st.button(label, key=f"sp_{i}", use_container_width=True):
                st.session_state.saved_idx = i

        st.divider()
        excel_bytes = _build_excel(saved_list, cfg)
        st.download_button(
            "⬇ Export Excel",
            data=excel_bytes,
            file_name=f"brand_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col_calc:
        idx = min(st.session_state.saved_idx, len(saved_list) - 1)
        s = saved_list[idx]
        sp_id = s["id"]

        if s.get("image_url"):
            st.image(s["image_url"], width=200)
        st.subheader(s["name"])
        st.markdown(f"**{s['site']}** · [{s.get('product_url', '')}]({s.get('product_url', '')})")

        st.divider()
        st.subheader("Calculator")

        col1, col2 = st.columns(2)
        transport = col1.number_input("Transport (lei)", value=float(s.get("transport_lei") or cfg["transport_lei"]), key=f"tr_{sp_id}")
        packaging = col2.number_input("Packaging (lei)", value=float(s.get("packaging_lei") or cfg["packaging_lei"]), key=f"pk_{sp_id}")
        fee_pct = st.number_input("Shopify fee (%)", value=float(s.get("platform_fee_pct") or cfg["platform_fee_pct"]), key=f"fee_{sp_id}")
        retail = st.number_input("Preț vânzare (lei) ✏️", value=float(s.get("retail_price_lei") or 0), step=10.0, key=f"ret_{sp_id}")
        notes = st.text_input("Note", value=s.get("notes") or "", key=f"nt_{sp_id}")

        if st.button("Actualizează", key=f"upd_{sp_id}"):
            update_saved_product_pricing(conn, sp_id, retail, transport, packaging, fee_pct, notes)
            st.rerun()

        if retail > 0:
            s_tmp = dict(s)
            s_tmp.update({"retail_price_lei": retail, "transport_lei": transport,
                          "packaging_lei": packaging, "platform_fee_pct": fee_pct})
            m = _calc(s_tmp, cfg)
            st.divider()
            col1, col2 = st.columns(2)
            col1.metric("Total cost", f"{m['total_cost']:.0f} lei")
            col2.metric("Marjă brută", f"{m['gross_margin']:.0f} lei ({m['gross_margin_pct']}%)")

            st.markdown("**Profit net per bucată după ads:**")
            c1, c2, c3 = st.columns(3)
            c1.metric("5 vânz/zi", f"{m['net_5']:.0f} lei")
            c2.metric("8 vânz/zi", f"{m['net_8']:.0f} lei")
            c3.metric("12 vânz/zi", f"{m['net_12']:.0f} lei")

            st.markdown("**Distribuție profit la 8 vânz/zi:**")
            c1, c2, c3 = st.columns(3)
            c1.metric(f"Tu ({int(cfg['partners']['user']*100)}%)", f"{m['user_8']:.0f} lei/zi")
            c2.metric(f"TREX ({int(cfg['partners']['trex']*100)}%)", f"{m['trex_8']:.0f} lei/zi")
            c3.metric(f"Partener ({int(cfg['partners']['partner2']*100)}%)", f"{m['partner2_8']:.0f} lei/zi")

            if m["breakeven_days"]:
                st.info(f"Break-even investiție (€2000): **~{m['breakeven_days']:.0f} zile** la 8 vânzări/zi")
