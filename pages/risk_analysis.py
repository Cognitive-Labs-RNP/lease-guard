"""
Risk Analysis page for LeaseGuard.

Portfolio and property-level risk assessment.
"""

from typing import Any, Dict

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from services.auth import get_supabase_client, require_current_user_id
from ui.custom_theme import get_color


def _get_risk_scores() -> list[Dict[str, Any]]:
    """Fetch all risk scores."""
    user_id = require_current_user_id()
    client = get_supabase_client()

    response = client.table("risk_scores").select("*").eq("user_id", user_id).order("calculated_at", desc=True).execute()
    return response.data or []


def _get_properties() -> list[Dict[str, Any]]:
    """Fetch user's properties."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("properties").select("id, name").eq("user_id", user_id).order("name").execute()
    return response.data or []


def _create_portfolio_risk_distribution():
    """Create portfolio risk level distribution chart."""
    scores = _get_risk_scores()
    risk_levels = [s.get("risk_level", "low") for s in scores]

    level_counts = {"critical": 0, "high": 0, "moderate": 0, "low": 0}
    for level in risk_levels:
        if level in level_counts:
            level_counts[level] += 1

    fig = go.Figure(
        data=[
            go.Bar(
                x=list(level_counts.keys()),
                y=list(level_counts.values()),
                marker=dict(
                    color=[
                        get_color("risk_critical"),
                        get_color("risk_high"),
                        get_color("risk_moderate"),
                        get_color("risk_low"),
                    ]
                ),
                text=list(level_counts.values()),
                textposition="auto",
            )
        ]
    )

    fig.update_layout(
        title="Portfolio Risk Distribution",
        xaxis_title="Risk Level",
        yaxis_title="Property Count",
        template="plotly_dark",
        plot_bgcolor=get_color("bg_secondary"),
        paper_bgcolor=get_color("bg_secondary"),
        font=dict(color=get_color("text_primary")),
        showlegend=False,
    )

    return fig


def _create_risk_score_distribution():
    """Create risk score distribution histogram."""
    scores = _get_risk_scores()
    score_values = [s.get("overall_score", 0) for s in scores]

    if not score_values:
        return None

    fig = go.Figure(
        data=[
            go.Histogram(
                x=score_values,
                nbinsx=10,
                marker=dict(color=get_color("accent_blue")),
            )
        ]
    )

    fig.update_layout(
        title="Risk Score Distribution",
        xaxis_title="Overall Score (0-100)",
        yaxis_title="Property Count",
        template="plotly_dark",
        plot_bgcolor=get_color("bg_secondary"),
        paper_bgcolor=get_color("bg_secondary"),
        font=dict(color=get_color("text_primary")),
        showlegend=False,
    )

    return fig


def _create_category_risk_chart():
    """Create category-level risk breakdown."""
    scores = _get_risk_scores()

    categories = {
        "CAM risk": [],
        "Rent escalation risk": [],
        "Administrative fee risk": [],
        "Tax risk": [],
        "Audit rights risk": [],
    }

    for score in scores:
        breakdown = score.get("score_breakdown", {})
        for cat in categories:
            if cat in breakdown:
                categories[cat].append(breakdown[cat])

    # Calculate averages
    category_avgs = {cat: sum(vals) / len(vals) if vals else 0 for cat, vals in categories.items()}

    fig = go.Figure(
        data=[
            go.Bar(
                x=list(category_avgs.keys()),
                y=list(category_avgs.values()),
                marker=dict(color=get_color("accent_orange")),
                text=[f"{v:.1f}" for v in category_avgs.values()],
                textposition="auto",
            )
        ]
    )

    fig.update_layout(
        title="Average Category Risk Scores",
        xaxis_title="Category",
        yaxis_title="Average Score",
        template="plotly_dark",
        plot_bgcolor=get_color("bg_secondary"),
        paper_bgcolor=get_color("bg_secondary"),
        font=dict(color=get_color("text_primary")),
        showlegend=False,
    )

    return fig


def render():
    """Render the risk analysis page."""
    st.markdown("## 📊 Risk Analysis")

    tab1, tab2 = st.tabs(["Portfolio Risk", "Property Risk"])

    with tab1:
        st.markdown("### Portfolio Risk Overview")

        scores = _get_risk_scores()

        if not scores:
            st.info("No risk scores calculated yet. Run audits to generate risk scores.")
            return

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        overall_avg = sum(s.get("overall_score", 0) for s in scores) / len(scores) if scores else 0

        with col1:
            st.metric("Avg Risk Score", f"{overall_avg:.1f}/100")

        with col2:
            critical = sum(1 for s in scores if s.get("risk_level") == "critical")
            st.metric("Critical", critical)

        with col3:
            high = sum(1 for s in scores if s.get("risk_level") == "high")
            st.metric("High", high)

        with col4:
            low = sum(1 for s in scores if s.get("risk_level") == "low")
            st.metric("Low", low)

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            fig_dist = _create_portfolio_risk_distribution()
            st.plotly_chart(fig_dist, use_container_width=True)

        with col2:
            fig_hist = _create_risk_score_distribution()
            if fig_hist:
                st.plotly_chart(fig_hist, use_container_width=True)

        # Category breakdown
        fig_cat = _create_category_risk_chart()
        st.plotly_chart(fig_cat, use_container_width=True)

    with tab2:
        st.markdown("### Property Risk Details")

        properties = _get_properties()
        prop_dict = {p["id"]: p["name"] for p in properties}

        if not properties:
            st.info("No properties yet")
            return

        # Create a detailed table
        rows = []
        for score in _get_risk_scores():
            prop_id = score.get("property_id")
            prop_name = prop_dict.get(prop_id, "Unknown")

            rows.append({
                "Property": prop_name,
                "Risk Score": score.get("overall_score", 0),
                "Risk Level": score.get("risk_level", "unknown"),
                "Calculated": score.get("calculated_at", "")[:10],
            })

        df = pd.DataFrame(rows)

        if not df.empty:
            # Sort by risk score descending
            df = df.sort_values("Risk Score", ascending=False)

            # Color code the table
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Detailed view
            selected_prop_name = st.selectbox(
                "Select property for details",
                options=df["Property"].unique(),
                key="prop_detail_select"
            )

            if selected_prop_name:
                # Find the score for this property
                selected_row = df[df["Property"] == selected_prop_name].iloc[0]

                st.markdown(f"### {selected_prop_name}")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Risk Score", f"{selected_row['Risk Score']:.0f}/100")
                with col2:
                    st.write(f"**Risk Level**: {selected_row['Risk Level']}")
                with col3:
                    st.write(f"**Last Calculated**: {selected_row['Calculated']}")

                # Find the detailed score for breakdown
                prop_id = next((p["id"] for p in properties if p["name"] == selected_prop_name), None)
                if prop_id:
                    score_data = next((s for s in _get_risk_scores() if s.get("property_id") == prop_id), None)
                    if score_data:
                        breakdown = score_data.get("score_breakdown", {})
                        if breakdown:
                            st.markdown("### Risk Category Breakdown")
                            for cat, val in breakdown.items():
                                st.write(f"{cat}: {val}")
        else:
            st.info("No risk scores available")
