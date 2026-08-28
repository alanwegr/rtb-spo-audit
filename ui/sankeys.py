"""Plotly Sankey: DSP -> SSP -> Publisher flow."""
import plotly.graph_objects as go


def sankey(df, source_col: str, target_col: str, value_col: str, title: str) -> go.Figure:
    """df: rows w/ source, target, value. auto-indexes unique nodes."""
    labels = list(dict.fromkeys(df[source_col].tolist() + df[target_col].tolist()))
    idx = {n: i for i, n in enumerate(labels)}
    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(pad=15, thickness=20, label=labels),
        link=dict(
            source=[idx[s] for s in df[source_col]],
            target=[idx[t] for t in df[target_col]],
            value=df[value_col],
        ),
    ))
    fig.update_layout(title_text=title, font_size=12, height=500)
    return fig
