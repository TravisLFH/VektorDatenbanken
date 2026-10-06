"""Gemeinsame Darstellung für Seiten und Plotly-Grafiken."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st


def inject_css() -> None:
    """Ergänzt nur Abstände, Karten und Zustandsfarben außerhalb der Standard-API."""
    st.markdown(
        """
        <style>
        /* Ruhiger Seitenkopf und gleichmäßige Abschnittsabstände. */
        .app-page-header { padding: 0.35rem 0 1.15rem; }
        .app-page-header h1 { margin-bottom: 0.2rem; }
        .app-page-header p { color: var(--text-color); opacity: 0.72; margin: 0; }
        /* Kennzeichnet den gerade bearbeiteten Eintrag ohne interne Streamlit-Klassen. */
        .editing-banner { border-left: 4px solid #0f766e; padding: 0.65rem 0.85rem; margin: 0.5rem 0 1rem; background: color-mix(in srgb, #0f766e 10%, transparent); }
        .technical-label { color: var(--text-color); font-family: var(--font); font-size: 0.72rem; opacity: 0.58; text-align: right; }
        .metadata-chips { display: flex; flex-wrap: wrap; gap: 0.35rem; margin: 0.15rem 0 0.35rem; }
        .metadata-chip { background: rgba(100, 116, 139, 0.13); border: 1px solid rgba(100, 116, 139, 0.2); border-radius: 999px; color: var(--text-color); font-size: 0.73rem; line-height: 1.35; padding: 0.12rem 0.5rem; opacity: 0.8; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_chart_style(fig: go.Figure, height: int = 460) -> go.Figure:
    """Wendet ein neutrales, hell- und dunkelmodus-taugliches Plotly-Layout an."""
    fig.update_layout(
        height=height,
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Source Sans 3, sans-serif", "size": 14, "color": "#24313a"},
        margin={"l": 20, "r": 20, "t": 55, "b": 20},
        legend={"orientation": "h", "y": -0.15},
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(100,116,139,0.18)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(100,116,139,0.18)", zeroline=False)
    return fig