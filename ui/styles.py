"""
Legacy styles compatibility module for LeaseGuard AI.
Delegates styling directly to ui.custom_theme.apply_custom_theme.
"""

import streamlit as st
from ui.custom_theme import apply_custom_theme


def load_css() -> None:
    """Apply the shared application styling."""
    apply_custom_theme()
