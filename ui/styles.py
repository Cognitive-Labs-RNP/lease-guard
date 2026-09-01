import streamlit as st


def load_css() -> None:
    """Apply the shared application styling."""
    st.markdown(
        """
        <style>
            :root {
                --bg: #0f172a;
                --panel: #111827;
                --card: #1f2937;
                --text: #e5e7eb;
                --muted: #94a3b8;
                --border: rgba(148, 163, 184, 0.2);
                --accent: #22c55e;
                --accent-soft: rgba(34, 197, 94, 0.12);
            }

            .stApp {
                background: linear-gradient(180deg, #0b1220 0%, #111827 100%);
                color: var(--text);
            }

            [data-testid="stSidebar"] {
                background: #0f172a;
                border-right: 1px solid var(--border);
            }

            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }

            div[data-testid="stMetric"] {
                background: rgba(17, 24, 39, 0.85);
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 1rem;
            }

            .stAlert,
            .stDataFrame,
            .stTabs [role="tablist"] {
                border-radius: 12px;
            }

            h1, h2, h3 {
                letter-spacing: -0.02em;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
