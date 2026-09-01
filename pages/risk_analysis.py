"""
Risk Analysis page for LeaseGuard AI.

Portfolio and property-level contractual risk assessment, risk distribution models,
and category-level risk breakdowns.
"""

from typing import Any, Dict, List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from services.auth import get_supabase_client, require_current_user_id
from ui.custom_theme import COLORS, get_color, get_plotly_layout_theme
from utils.ui import (
    render_divider,
    render_empty_state,
    render_kpi_card,
    render_page_header,
    render_section_header,
    render_status_badge,
)


def _get_risk_scores() -> List[Dict[str, Any]]:
    """Fetch all calculated risk scores."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("risk_scores").select("*").eq("user_id", user_id).order("calculated_at", desc=True).execute()
    return response.data or []


def _get_properties() -> List[Dict[str, Any]]:
    """Fetch user's properties."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("properties").select("id, name").eq("user_id", user_id).order("name").execute()
    return response.data or []


def _create_portfolio_risk_distribution(scores: List[Dict[str, Any]]):
    """Create portfolio risk level distribution bar chart."""
    level_counts = {"critical": 0, "high": 0, "moderate": 0, "low": 0}
    for s in scores:
        level = (s.get("risk_level") or "low").lower()
        if level in level_counts:
            level_counts[level] += 1

    labels = ["Critical Risk", "High Risk", "Moderate Risk", "Low Risk"]
    counts = [level_counts["critical"], level_counts["high"], level_counts["moderate"], level_counts["low"]]
    colors = [
        get_color("risk_critical"),
        get_color("risk_high"),
        get_color("risk_moderate"),
        get_color("risk_low"),
    ]

    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=counts,
                marker=dict(color=colors, line=dict(color="rgba(0,0,0,0.05)", width=1)),
                text=counts,
                textposition="outside",
            )
        ]
    )

    layout = get_plotly_layout_theme()
    layout.update(
        title=dict(text="Portfolio Risk Classification Distribution", font=dict(size=14, color="#172033")),
        xaxis_title="Risk Tier",
        yaxis_title="Property Count",
        height=320,
    )
    fig.update_layout(layout)
    return fig


def _create_category_risk_chart(scores: List[Dict[str, Any]]):
    """Create average score by risk category bar chart from persisted breakdowns."""
    categories = {
        "CAM Risk": [],
        "Rent Escalation": [],
        "Administrative Fee": [],
        "Tax Exposure": [],
        "Audit Rights": [],
    }

    key_map = {
        "cam_risk": "CAM Risk",
        "rent_escalation_risk": "Rent Escalation",
        "administrative_fee_risk": "Administrative Fee",
        "tax_risk": "Tax Exposure",
        "audit_rights_risk": "Audit Rights",
    }

    for score in scores:
        breakdown = score.get("score_breakdown", {})
        if isinstance(breakdown, dict):
            for raw_k, display_k in key_map.items():
                if raw_k in breakdown:
                    categories[display_k].append(float(breakdown[raw_k]))

    category_avgs = {cat: (sum(vals) / len(vals) if vals else 0.0) for cat, vals in categories.items()}

    fig = go.Figure(
        data=[
            go.Bar(
                x=list(category_avgs.keys()),
                y=list(category_avgs.values()),
                marker=dict(
                    color=[
                        get_color("brand_blue"),
                        get_color("brand_teal"),
                        get_color("warning"),
                        get_color("accent_orange"),
                        "#6366F1",
                    ]
                ),
                text=[f"{v:.1f} pts" for v in category_avgs.values()],
                textposition="outside",
            )
        ]
    )

    layout = get_plotly_layout_theme()
    layout.update(
        title=dict(text="Average Risk Exposure by Category (0-100)", font=dict(size=14, color="#172033")),
        xaxis_title="Contract Area",
        yaxis_title="Average Risk Score",
        height=320,
    )
    fig.update_layout(layout)
    return fig


def render():
    """Render the comprehensive risk analysis view."""
    render_page_header(
        title="Portfolio Risk Exposure",
        subtitle="Evaluate contractual vulnerability, lease non-compliance rates, and categorical risk distributions.",
        icon="📊",
    )

    scores = _get_risk_scores()
    properties = _get_properties()
    prop_dict = {p["id"]: p["name"] for p in properties}

    if not scores:
        render_empty_state(
            title="No Risk Evaluations Computed",
            description="Execute deterministic audit sessions to calculate risk scores and evaluate portfolio vulnerabilities.",
            icon="📊",
        )
        return

    tab_portfolio, tab_property = st.tabs(["Portfolio Risk Overview", "Property Risk Breakdown"])

    # -----------------------------------------------------------------------
    # TAB 1: PORTFOLIO RISK
    # -----------------------------------------------------------------------
    with tab_portfolio:
        overall_avg = sum(s.get("overall_score", 0) for s in scores) / len(scores) if scores else 0.0
        critical_count = sum(1 for s in scores if (s.get("risk_level") or "").lower() == "critical")
        high_count = sum(1 for s in scores if (s.get("risk_level") or "").lower() == "high")
        mod_count = sum(1 for s in scores if (s.get("risk_level") or "").lower() == "moderate")
        low_count = sum(1 for s in scores if (s.get("risk_level") or "").lower() == "low")

        render_section_header("Portfolio Health Index", "Aggregated risk profile across all audited commercial properties")

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            render_kpi_card("Average Risk Score", f"{overall_avg:.1f} / 100", "Portfolio aggregate", "📊", get_color("brand_blue"))
        with c2:
            render_kpi_card("Critical Risk", str(critical_count), "Requires immediate intervention", "🔴", get_color("risk_critical"))
        with c3:
            render_kpi_card("High Risk", str(high_count), "Substantial overcharges", "🟠", get_color("risk_high"))
        with c4:
            render_kpi_card("Moderate Risk", str(mod_count), "Minor variances", "🟡", get_color("risk_moderate"))
        with c5:
            render_kpi_card("Low Risk", str(low_count), "Compliant billing", "🟢", get_color("risk_low"))

        st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig_dist = _create_portfolio_risk_distribution(scores)
            st.plotly_chart(fig_dist, use_container_width=True)

        with col_g2:
            fig_cat = _create_category_risk_chart(scores)
            st.plotly_chart(fig_cat, use_container_width=True)

    # -----------------------------------------------------------------------
    # TAB 2: PROPERTY RISK DETAILS
    # -----------------------------------------------------------------------
    with tab_property:
        render_section_header("Property Risk Matrix", "Detailed risk assessment metrics per individual real estate asset")

        rows = []
        for score in scores:
            p_id = score.get("property_id")
            p_name = prop_dict.get(p_id, "Unknown Property")
            score_val = float(score.get("overall_score", 0.0))
            level = score.get("risk_level", "low").upper()

            rows.append({
                "Property": p_name,
                "Risk Score": f"{score_val:.0f} / 100",
                "Risk Rating": level,
                "Audit Date": score.get("calculated_at", "")[:10],
            })

        df = pd.DataFrame(rows)
        if not df.empty:
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            render_section_header("Category Drilldown by Property", "Inspect score breakdown for a specific property")

            selected_prop_name = st.selectbox(
                "Select Property for In-Depth Risk Inspection",
                options=df["Property"].unique(),
                key="prop_risk_drilldown",
            )

            if selected_prop_name:
                p_id_match = next((p["id"] for p in properties if p["name"] == selected_prop_name), None)
                if p_id_match:
                    score_match = next((s for s in scores if s.get("property_id") == p_id_match), None)
                    if score_match:
                        with st.container(border=True):
                            sc1, sc2 = st.columns([1, 2])
                            with sc1:
                                s_val = float(score_match.get("overall_score", 0))
                                st.markdown(
                                    f"""
                                    <div style="text-align:center; padding:1rem 0;">
                                        <div style="font-size:0.75rem; font-weight:700; color:#64748B; text-transform:uppercase;">Overall Property Risk</div>
                                        <div style="font-size:3rem; font-weight:800; color:#172033; letter-spacing:-0.04em;">{s_val:.0f}<span style="font-size:1.25rem; color:#94A3B8;">/100</span></div>
                                        <div>{render_status_badge(score_match.get('risk_level', 'low'))}</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                            with sc2:
                                breakdown = score_match.get("score_breakdown", {})
                                if isinstance(breakdown, dict) and breakdown:
                                    st.markdown("<strong>Risk Dimension Breakdown:</strong>", unsafe_allow_html=True)
                                    for cat_key, cat_val in breakdown.items():
                                        clean_name = cat_key.replace("_", " ").title()
                                        st.write(f"• **{clean_name}**: {cat_val:.0f} pts")
                                else:
                                    st.info("No categorical sub-scores recorded for this session.")
        else:
            render_empty_state("No Property Risk Data", "Conduct audit sessions to populate this table.", "📊")
