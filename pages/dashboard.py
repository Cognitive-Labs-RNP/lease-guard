"""
Dashboard page for LeaseGuard.

Shows portfolio KPIs, risk summary, recovery tracking, and recent findings.
"""

from typing import Any, Dict

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from services.auth import get_supabase_client, require_current_user_id
from services.demo import is_demo_mode
from ui.custom_theme import COLORS, get_color


def _get_portfolio_kpis() -> Dict[str, Any]:
    """Fetch portfolio KPI metrics."""
    user_id = require_current_user_id()
    client = get_supabase_client()

    # Total properties
    props = client.table("properties").select("COUNT", count="exact").eq("user_id", user_id).execute()
    total_properties = props.count or 0

    # Total audits
    audits = client.table("audits").select("COUNT", count="exact").eq("user_id", user_id).execute()
    total_audits = audits.count or 0

    # Total findings
    findings = client.table("findings").select("COUNT", count="exact").eq("user_id", user_id).execute()
    total_findings = findings.count or 0

    # Potential recovery (sum of all finding amounts)
    finding_rows = client.table("findings").select("amount").eq("user_id", user_id).execute()
    potential_recovery = sum(float(f.get("amount", 0)) for f in (finding_rows.data or []))

    # Recovered amount (sum of recovery records marked as Recovered)
    recovery_rows = (
        client.table("recovery_records")
        .select("amount")
        .eq("user_id", user_id)
        .eq("status", "Recovered")
        .execute()
    )
    recovered_amount = sum(float(r.get("amount", 0)) for r in (recovery_rows.data or []))

    return {
        "total_properties": total_properties,
        "total_audits": total_audits,
        "total_findings": total_findings,
        "potential_recovery": potential_recovery,
        "recovered_amount": recovered_amount,
    }


def _get_portfolio_risk() -> Dict[str, Any]:
    """Fetch portfolio risk summary."""
    user_id = require_current_user_id()
    client = get_supabase_client()

    # Overall risk score (average)
    risk_scores = client.table("risk_scores").select("overall_score").eq("user_id", user_id).execute()
    scores = [float(r.get("overall_score", 0)) for r in (risk_scores.data or [])]
    overall_score = sum(scores) / len(scores) if scores else 0

    # Risk level distribution
    level_counts = {"critical": 0, "high": 0, "moderate": 0, "low": 0}
    for r in risk_scores.data or []:
        level = r.get("risk_level", "low").lower()
        if level in level_counts:
            level_counts[level] += 1

    # Properties with high risk
    high_risk_props = client.table("risk_scores").select("COUNT", count="exact").eq("user_id", user_id).gte(
        "overall_score", 60
    ).execute()
    high_risk_count = high_risk_props.count or 0

    return {
        "overall_score": round(overall_score, 1),
        "critical": level_counts["critical"],
        "high": level_counts["high"],
        "moderate": level_counts["moderate"],
        "low": level_counts["low"],
        "high_risk_properties": high_risk_count,
    }


def _get_recovery_tracking() -> Dict[str, Any]:
    """Fetch recovery status tracking."""
    user_id = require_current_user_id()
    client = get_supabase_client()

    # Potential recovery
    potential = client.table("recovery_records").select("amount").eq("user_id", user_id).execute()
    potential_total = sum(float(r.get("amount", 0)) for r in (potential.data or []))

    # Disputed
    disputed = (
        client.table("recovery_records")
        .select("amount")
        .eq("user_id", user_id)
        .eq("status", "Disputed")
        .execute()
    )
    disputed_total = sum(float(r.get("amount", 0)) for r in (disputed.data or []))

    # Under review
    under_review = (
        client.table("recovery_records")
        .select("amount")
        .eq("user_id", user_id)
        .eq("status", "Under Review")
        .execute()
    )
    under_review_total = sum(float(r.get("amount", 0)) for r in (under_review.data or []))

    # Recovered
    recovered = (
        client.table("recovery_records")
        .select("amount")
        .eq("user_id", user_id)
        .eq("status", "Recovered")
        .execute()
    )
    recovered_total = sum(float(r.get("amount", 0)) for r in (recovered.data or []))

    return {
        "potential": potential_total,
        "disputed": disputed_total,
        "under_review": under_review_total,
        "recovered": recovered_total,
    }


def _get_findings_by_category() -> pd.DataFrame:
    """Fetch findings grouped by category."""
    user_id = require_current_user_id()
    client = get_supabase_client()

    findings = client.table("findings").select("category").eq("user_id", user_id).execute()
    categories = {}
    for f in findings.data or []:
        cat = f.get("category", "Other")
        categories[cat] = categories.get(cat, 0) + 1

    return pd.DataFrame({"Category": list(categories.keys()), "Count": list(categories.values())})


def _get_high_risk_properties() -> pd.DataFrame:
    """Fetch high-risk properties."""
    user_id = require_current_user_id()
    client = get_supabase_client()

    # Get risk scores with property info
    risk_data = (
        client.table("risk_scores")
        .select("property_id, overall_score, risk_level")
        .eq("user_id", user_id)
        .gte("overall_score", 50)
        .order("overall_score", desc=True)
        .limit(10)
        .execute()
    )

    rows = []
    for risk in risk_data.data or []:
        prop_id = risk.get("property_id")
        prop = client.table("properties").select("name").eq("id", prop_id).execute()
        prop_name = (prop.data or [{}])[0].get("name", "Unknown") if prop.data else "Unknown"

        findings = (
            client.table("findings")
            .select("COUNT", count="exact")
            .eq("property_id", prop_id)
            .execute()
        )
        finding_count = findings.count or 0

        recovery = (
            client.table("recovery_records")
            .select("amount")
            .eq("property_id", prop_id)
            .execute()
        )
        recovery_amount = sum(float(r.get("amount", 0)) for r in (recovery.data or []))

        rows.append(
            {
                "Property": prop_name,
                "Risk Score": risk.get("overall_score", 0),
                "Risk Level": risk.get("risk_level", "unknown"),
                "Findings": finding_count,
                "Potential Recovery": f"${recovery_amount:,.2f}",
            }
        )

    return pd.DataFrame(rows)


def _get_recent_findings() -> pd.DataFrame:
    """Fetch recent findings."""
    user_id = require_current_user_id()
    client = get_supabase_client()

    findings = (
        client.table("findings")
        .select("category, title, severity, amount, status, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(10)
        .execute()
    )

    rows = []
    for f in findings.data or []:
        rows.append(
            {
                "Category": f.get("category", ""),
                "Title": f.get("title", ""),
                "Severity": f.get("severity", ""),
                "Amount": f"${float(f.get('amount', 0)):,.2f}",
                "Status": f.get("status", ""),
                "Date": f.get("created_at", "")[:10],
            }
        )

    return pd.DataFrame(rows)


def _create_recovery_timeline_chart():
    """Create recovery tracking chart."""
    user_id = require_current_user_id()
    client = get_supabase_client()

    recovery = client.table("recovery_records").select("status, amount").eq("user_id", user_id).execute()

    data = {"status": [], "amount": []}

    for r in recovery.data or []:
        status = r.get("status", "Detected")
        amount = float(r.get("amount", 0))
        data["status"].append(status)
        data["amount"].append(amount)

    df = pd.DataFrame(data)
    status_totals = df.groupby("status")["amount"].sum() if not df.empty else pd.Series()

    fig = go.Figure()
    if not status_totals.empty:
        fig.add_trace(
            go.Bar(
                x=status_totals.index,
                y=status_totals.values,
                marker=dict(
                    color=[
                        get_color("accent_blue"),
                        get_color("accent_orange"),
                        get_color("accent_yellow"),
                        get_color("accent_green"),
                    ][:len(status_totals)],
                ),
                text=[f"${v:,.0f}" for v in status_totals.values],
                textposition="auto",
            )
        )

    fig.update_layout(
        title="Recovery Pipeline Status",
        xaxis_title="Status",
        yaxis_title="Amount ($)",
        hovermode="x unified",
        template="plotly_dark",
        plot_bgcolor=get_color("bg_secondary"),
        paper_bgcolor=get_color("bg_secondary"),
        font=dict(color=get_color("text_primary"), family="Arial, sans-serif"),
        margin=dict(l=50, r=50, t=50, b=50),
    )

    return fig


def _create_findings_chart(df: pd.DataFrame):
    """Create findings by category chart."""
    fig = px.pie(
        df,
        values="Count",
        names="Category",
        title="Findings by Category",
        color_discrete_sequence=[
            get_color("accent_blue"),
            get_color("accent_orange"),
            get_color("accent_green"),
            get_color("risk_critical"),
            get_color("accent_yellow"),
        ],
    )

    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor=get_color("bg_secondary"),
        paper_bgcolor=get_color("bg_secondary"),
        font=dict(color=get_color("text_primary"), family="Arial, sans-serif"),
    )

    return fig


def render():
    """Render the dashboard page."""
    st.markdown("## 📊 Dashboard")

    if is_demo_mode():
        st.info("🎭 **DEMO MODE** — Using sample data for demonstration")

    # Load data
    kpis = _get_portfolio_kpis()
    risk = _get_portfolio_risk()
    recovery = _get_recovery_tracking()

    # Portfolio KPIs
    st.markdown("### Portfolio Overview")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Properties", kpis["total_properties"])

    with col2:
        st.metric("Audits", kpis["total_audits"])

    with col3:
        st.metric("Findings", kpis["total_findings"])

    with col4:
        st.metric("Potential Recovery", f"${kpis['potential_recovery']:,.2f}")

    with col5:
        st.metric("Recovered", f"${kpis['recovered_amount']:,.2f}")

    # Portfolio Risk
    st.markdown("### Portfolio Risk")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Overall Risk", f"{risk['overall_score']}/100")

    with col2:
        st.metric("Critical", risk["critical"])

    with col3:
        st.metric("High", risk["high"])

    with col4:
        st.metric("Moderate", risk["moderate"])

    with col5:
        st.metric("Low", risk["low"])

    # Recovery Tracking
    st.markdown("### Recovery Pipeline")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Potential", f"${recovery['potential']:,.2f}")

    with col2:
        st.metric("Disputed", f"${recovery['disputed']:,.2f}")

    with col3:
        st.metric("Under Review", f"${recovery['under_review']:,.2f}")

    with col4:
        st.metric("Recovered", f"${recovery['recovered']:,.2f}")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        fig_recovery = _create_recovery_timeline_chart()
        st.plotly_chart(fig_recovery, use_container_width=True)

    with col2:
        df_findings = _get_findings_by_category()
        if not df_findings.empty:
            fig_findings = _create_findings_chart(df_findings)
            st.plotly_chart(fig_findings, use_container_width=True)
        else:
            st.info("No findings yet")

    # High-Risk Properties
    st.markdown("### High-Risk Properties")
    df_high_risk = _get_high_risk_properties()
    if not df_high_risk.empty:
        st.dataframe(df_high_risk, use_container_width=True, hide_index=True)
    else:
        st.info("No high-risk properties")

    # Recent Findings
    st.markdown("### Recent Findings")
    df_recent = _get_recent_findings()
    if not df_recent.empty:
        st.dataframe(df_recent, use_container_width=True, hide_index=True)
    else:
        st.info("No findings yet")
