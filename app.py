"""Streamlit entry. Tiny orchestrator: generate -> load -> audit -> render."""
import streamlit as st
import pandas as pd

from config import SCENARIOS
from engine import db, generator, validator
from ui.components import kpi_row, section
from ui.sankeys import sankey

st.set_page_config(page_title="SPO & Margin Audit", layout="wide")
st.title("SPO & Margin Audit Engine")


@st.cache_resource(show_spinner="Loading auction stream...")
def load(scenario: str, n: int, seed: int):
    conn = db.fresh()
    db.load_jsonl(generator.stream(n, scenario, seed=seed), conn)
    db.build_views(conn)
    return conn


with st.sidebar:
    scenario = st.selectbox("Scenario", list(SCENARIOS),
                            format_func=lambda s: f"{s}: {SCENARIOS[s]}")
    n_auctions = st.slider("Batch size", 100, 10_000, 1000, step=100)
    seed = st.number_input("Seed", value=42)

conn = load(scenario, n_auctions, int(seed))

# KPIs
margins = pd.DataFrame(validator.margin_audit(conn))
dup = validator.duplication_audit(conn)
schain_rows = validator.schain_audit(conn)
unverified = sum(1 for r in schain_rows if r[7] in ("unverified", "unknown_seller", "unauthorized_reseller"))

kpi_row([
    ("Avg Take Rate", f"{(margins['avg_take_rate'].mean() * 100):.1f}%",
     f"target: {15}%"),
    ("Unverified Paths", unverified, f"of {len(schain_rows)} nodes"),
    ("Duplication Ratio", f"{dup[3]}x", f"{dup[1]} responses / {dup[2]} auctions"),
    ("Flagged Margins", int(margins["flagged"].sum()), f"of {len(margins)} SSPs"),
])

# Sankey
section("Supply Path Flow")
flow = pd.read_sql("SELECT dsp AS source, ssp AS target, COUNT(*) AS value "
                   "FROM v_auctions GROUP BY dsp, ssp", conn)
if not flow.empty:
    st.plotly_chart(sankey(flow, "source", "target", "value", "DSP → SSP Volume"), use_container_width=True)

# Margin table
section("Margin Audit")
st.dataframe(margins, use_container_width=True, hide_index=True)

# schain flags
section("schain Compliance")
flag_df = pd.DataFrame(schain_rows, columns=[
    "auction_id", "asi", "sid", "hop", "seller_type", "is_confidential", "flag"
])
st.dataframe(flag_df[flag_df["flag"] != "ok"], use_container_width=True, hide_index=True)
