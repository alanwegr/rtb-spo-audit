"""KPI cards. streamlit is stdlib of dashboards."""
import streamlit as st


def kpi_row(metrics: list[tuple[str, str | float, str]]) -> None:
    """metrics: [(label, value, delta_str), ...]"""
    cols = st.columns(len(metrics))
    for c, (label, val, delta) in zip(cols, metrics):
        c.metric(label, val, delta)


def section(title: str) -> None:
    st.markdown(f"### {title}")
    st.divider()
