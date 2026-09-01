"""
Custom Streamlit theme configuration and CSS for LeaseGuard AI.

Enterprise SaaS aesthetic:
  - Light neutral workspace background (#F5F7FB)
  - Dark navy sidebar navigation (#0F172A)
  - White cards with subtle shadow/border (#FFFFFF)
  - Blue / teal primary actions (#1D4ED8 / #0891B2)
  - Green / amber / red semantic status colors
"""

import os
from pathlib import Path
from typing import Any, Dict
import streamlit as st

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------

COLORS = {
    # Workspace backgrounds
    "bg_workspace":     "#F5F7FB",   # Main page background (light neutral)
    "bg_card":          "#FFFFFF",   # Card / surface
    "bg_sidebar":       "#0F172A",   # Dark navy sidebar
    "bg_sidebar_hover": "#1E293B",   # Sidebar item hover
    "bg_sidebar_active":"#1D4ED8",   # Sidebar active item

    # Backward compatibility keys
    "bg_primary":       "#F5F7FB",
    "bg_secondary":     "#FFFFFF",
    "bg_tertiary":      "#F1F5F9",

    # Text
    "text_primary":     "#172033",   # Dark navy / charcoal
    "text_secondary":   "#667085",   # Muted gray
    "text_inverse":     "#F8FAFC",   # Light text on dark bg
    "text_sidebar":     "#CBD5E1",   # Sidebar text

    # Brand / primary actions
    "brand_navy":       "#0F172A",
    "brand_blue":       "#1D4ED8",   # Primary CTA blue
    "brand_teal":       "#0891B2",   # Accent teal

    # Accents
    "accent_blue":      "#1D4ED8",
    "accent_green":     "#16A34A",
    "accent_red":       "#DC2626",
    "accent_orange":    "#D97706",
    "accent_yellow":    "#CA8A04",
    "accent_teal":      "#0891B2",

    # Semantic status
    "success":          "#16A34A",   # Green
    "warning":          "#D97706",   # Amber
    "danger":           "#DC2626",   # Red
    "info":             "#0284C7",   # Blue/Teal

    # Risk levels
    "risk_critical":    "#DC2626",
    "risk_high":        "#EA580C",
    "risk_moderate":    "#D97706",
    "risk_low":         "#16A34A",

    # Border
    "border":           "#E2E8F0",
    "border_strong":    "#CBD5E1",
}


def _load_stylesheet() -> str:
    """Read the centralized CSS stylesheet from assets/styles.css."""
    css_path = Path(__file__).resolve().parent.parent / "assets" / "styles.css"
    if css_path.exists():
        try:
            return css_path.read_text(encoding="utf-8")
        except Exception:
            pass
    return ""


def apply_custom_theme() -> None:
    """Apply centralized enterprise CSS theme to the Streamlit app."""
    css_content = _load_stylesheet()
    if css_content:
        st.markdown(f"<style>\n{css_content}\n</style>", unsafe_allow_html=True)


def get_color(color_key: str) -> str:
    """Get a color hex code from the enterprise palette."""
    return COLORS.get(color_key, COLORS["text_primary"])


def get_plotly_layout_theme() -> Dict[str, Any]:
    """
    Standardized Plotly chart layout matching the light enterprise workspace.

    Avoids dark Plotly backgrounds in the light UI.
    """
    return {
        "template": "plotly_white",
        "paper_bgcolor": "#FFFFFF",
        "plot_bgcolor": "#FFFFFF",
        "font": {
            "family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif",
            "color": "#172033",
            "size": 12,
        },
        "margin": {"l": 40, "r": 20, "t": 48, "b": 40},
        "xaxis": {
            "gridcolor": "#F1F5F9",
            "linecolor": "#E2E8F0",
            "tickcolor": "#CBD5E1",
            "title_font": {"size": 12, "color": "#667085"},
            "tickfont": {"size": 11, "color": "#667085"},
        },
        "yaxis": {
            "gridcolor": "#F1F5F9",
            "linecolor": "#E2E8F0",
            "tickcolor": "#CBD5E1",
            "title_font": {"size": 12, "color": "#667085"},
            "tickfont": {"size": 11, "color": "#667085"},
        },
        "legend": {
            "font": {"size": 11, "color": "#172033"},
            "bgcolor": "rgba(255, 255, 255, 0.8)",
            "bordercolor": "#E2E8F0",
            "borderwidth": 1,
        },
    }
