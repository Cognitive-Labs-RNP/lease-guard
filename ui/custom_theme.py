"""
Custom Streamlit theme configuration and CSS for LeaseGuard.

Dark/indie-premium aesthetic with data-dense layout.
"""

# Color palette
COLORS = {
    "bg_primary": "#0F1419",      # Dark navy-black
    "bg_secondary": "#1A1F2E",    # Slightly lighter
    "bg_tertiary": "#242A3F",     # Tertiary bg
    "text_primary": "#E8E8E8",    # Off-white
    "text_secondary": "#A0A0A0",  # Gray
    "border": "#2A3142",          # Subtle border
    "accent_blue": "#00A8E8",     # Cyan-blue
    "accent_green": "#00D084",    # Emerald green
    "accent_red": "#FF4C4C",      # Error red
    "accent_orange": "#FFA500",   # Warning orange
    "accent_yellow": "#FFD700",   # Info yellow
    "risk_critical": "#FF4C4C",
    "risk_high": "#FFA500",
    "risk_moderate": "#FFD700",
    "risk_low": "#00D084",
}

CUSTOM_CSS = f"""
<style>
:root {{
    --bg-primary: {COLORS["bg_primary"]};
    --bg-secondary: {COLORS["bg_secondary"]};
    --bg-tertiary: {COLORS["bg_tertiary"]};
    --text-primary: {COLORS["text_primary"]};
    --text-secondary: {COLORS["text_secondary"]};
    --border: {COLORS["border"]};
    --accent-blue: {COLORS["accent_blue"]};
    --accent-green: {COLORS["accent_green"]};
    --accent-red: {COLORS["accent_red"]};
}}

/* Base styles */
body {{
    background-color: {COLORS["bg_primary"]};
    color: {COLORS["text_primary"]};
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
}}

/* Main container */
.main {{
    background-color: {COLORS["bg_primary"]};
    color: {COLORS["text_primary"]};
}}

/* Sidebar */
.css-1d391kg {{
    background-color: {COLORS["bg_secondary"]};
}}

.css-1lcbmhc {{
    background-color: {COLORS["bg_secondary"]};
}}

/* Navigation section */
.css-1y0tads {{
    background-color: {COLORS["bg_secondary"]};
}}

/* Buttons */
.stButton > button {{
    background-color: {COLORS["accent_blue"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["accent_blue"]};
    border-radius: 6px;
    font-weight: 600;
    transition: all 0.2s ease;
    padding: 0.5rem 1rem;
}}

.stButton > button:hover {{
    background-color: {COLORS["accent_blue"]};
    opacity: 0.9;
    transform: translateY(-2px);
}}

.stButton > button:active {{
    transform: translateY(0);
}}

/* Secondary button style */
.stButton.secondary > button {{
    background-color: {COLORS["bg_tertiary"]};
    border: 1px solid {COLORS["border"]};
}}

.stButton.secondary > button:hover {{
    background-color: {COLORS["border"]};
}}

/* Input fields */
.stTextInput input,
.stSelectbox select,
.stNumberInput input,
.stDateInput input,
.stFileUploader {{
    background-color: {COLORS["bg_secondary"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
}}

.stTextInput input:focus,
.stSelectbox select:focus,
.stNumberInput input:focus {{
    border-color: {COLORS["accent_blue"]};
    box-shadow: 0 0 0 2px {COLORS["accent_blue"]}22;
}}

/* Cards and containers */
.css-uce5v8 {{
    background-color: {COLORS["bg_secondary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 1.5rem;
}}

/* Metric cards (using custom component) */
.metric-card {{
    background: linear-gradient(135deg, {COLORS["bg_secondary"]} 0%, {COLORS["bg_tertiary"]} 100%);
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}}

.metric-label {{
    color: {COLORS["text_secondary"]};
    font-size: 0.875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.metric-value {{
    color: {COLORS["text_primary"]};
    font-size: 2rem;
    font-weight: 700;
    line-height: 1;
}}

.metric-change {{
    color: {COLORS["accent_green"]};
    font-size: 0.75rem;
    font-weight: 600;
}}

.metric-change.negative {{
    color: {COLORS["accent_red"]};
}}

/* Risk badges */
.risk-badge {{
    display: inline-block;
    padding: 0.35rem 0.75rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.risk-badge.critical {{
    background-color: {COLORS["risk_critical"]}20;
    color: {COLORS["risk_critical"]};
    border: 1px solid {COLORS["risk_critical"]}40;
}}

.risk-badge.high {{
    background-color: {COLORS["risk_high"]}20;
    color: {COLORS["risk_high"]};
    border: 1px solid {COLORS["risk_high"]}40;
}}

.risk-badge.moderate {{
    background-color: {COLORS["risk_moderate"]}20;
    color: {COLORS["risk_moderate"]};
    border: 1px solid {COLORS["risk_moderate"]}40;
}}

.risk-badge.low {{
    background-color: {COLORS["risk_low"]}20;
    color: {COLORS["risk_low"]};
    border: 1px solid {COLORS["risk_low"]}40;
}}

/* Finding cards */
.finding-card {{
    background-color: {COLORS["bg_secondary"]};
    border-left: 4px solid {COLORS["accent_blue"]};
    border-radius: 6px;
    padding: 1.25rem;
    margin-bottom: 1rem;
}}

.finding-category {{
    color: {COLORS["accent_blue"]};
    font-size: 0.875rem;
    font-weight: 700;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}}

.finding-title {{
    color: {COLORS["text_primary"]};
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}}

.finding-description {{
    color: {COLORS["text_secondary"]};
    font-size: 0.875rem;
    line-height: 1.5;
    margin-bottom: 1rem;
}}

.finding-recovery {{
    color: {COLORS["accent_green"]};
    font-size: 0.875rem;
    font-weight: 600;
}}

/* Tables */
.stDataFrame {{
    background-color: {COLORS["bg_secondary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
}}

/* Charts (Plotly) */
.plotly-chart {{
    background-color: {COLORS["bg_secondary"]};
    border-radius: 8px;
    padding: 1rem;
}}

/* Section headers */
.section-header {{
    color: {COLORS["text_primary"]};
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 1.5rem;
    border-bottom: 2px solid {COLORS["border"]};
    padding-bottom: 1rem;
}}

/* Subsection headers */
.subsection-header {{
    color: {COLORS["text_primary"]};
    font-size: 1.125rem;
    font-weight: 600;
    margin-top: 1.5rem;
    margin-bottom: 1rem;
}}

/* Info box */
.info-box {{
    background-color: {COLORS["accent_blue"]}15;
    border-left: 4px solid {COLORS["accent_blue"]};
    border-radius: 6px;
    padding: 1rem;
    margin: 1rem 0;
}}

.info-box-text {{
    color: {COLORS["text_secondary"]};
    font-size: 0.875rem;
    line-height: 1.5;
}}

/* Success box */
.success-box {{
    background-color: {COLORS["accent_green"]}15;
    border-left: 4px solid {COLORS["accent_green"]};
    border-radius: 6px;
    padding: 1rem;
    margin: 1rem 0;
}}

/* Warning box */
.warning-box {{
    background-color: {COLORS["risk_high"]}15;
    border-left: 4px solid {COLORS["risk_high"]};
    border-radius: 6px;
    padding: 1rem;
    margin: 1rem 0;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    background-color: transparent;
    border-bottom: 2px solid {COLORS["border"]};
    gap: 2rem;
}}

.stTabs [data-baseweb="tab"] {{
    color: {COLORS["text_secondary"]};
    border-bottom: 3px solid transparent;
}}

.stTabs [aria-selected="true"] {{
    color: {COLORS["accent_blue"]};
    border-bottom-color: {COLORS["accent_blue"]};
}}

/* Expandable sections */
.streamlit-expanderHeader {{
    background-color: {COLORS["bg_tertiary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
}}

/* Spacing utilities */
.spacing-sm {{ margin: 0.5rem 0; }}
.spacing-md {{ margin: 1rem 0; }}
.spacing-lg {{ margin: 1.5rem 0; }}
.spacing-xl {{ margin: 2rem 0; }}

/* Grid layout */
.grid-2 {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
}}

.grid-3 {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
}}

.grid-4 {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.5rem;
}}

@media (max-width: 1200px) {{
    .grid-4 {{ grid-template-columns: repeat(2, 1fr); }}
}}

@media (max-width: 768px) {{
    .grid-2, .grid-3, .grid-4 {{ grid-template-columns: 1fr; }}
}}

/* Text utilities */
.text-muted {{ color: {COLORS["text_secondary"]}; }}
.text-accent {{ color: {COLORS["accent_blue"]}; }}
.text-success {{ color: {COLORS["accent_green"]}; }}
.text-danger {{ color: {COLORS["risk_critical"]}; }}

.font-mono {{
    font-family: 'Monaco', 'Courier New', monospace;
    background-color: {COLORS["bg_tertiary"]};
    padding: 0.25rem 0.5rem;
    border-radius: 3px;
    font-size: 0.875rem;
}}

/* Truncate overflow */
.truncate {{
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}}

.truncate-2 {{
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}}
</style>
"""


def apply_custom_theme():
    """Apply custom CSS theme to Streamlit app."""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def get_color(color_key: str) -> str:
    """Get a color from the palette."""
    return COLORS.get(color_key, COLORS["text_primary"])
