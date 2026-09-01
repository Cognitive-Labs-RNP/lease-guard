"""
Dashboard page for LeaseGuard AI.

Provides high-level portfolio KPIs, risk summary, recovery pipeline tracking,
and actionable audit findings.
"""

from typing import Any, Dict
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from services.auth import get_supabase_client, require_current_user_id
from services.demo import is_demo_mode
from ui.custom_theme import COLORS, get_color, get_plotly_layout_theme
from utils.ui import (
    format_currency,
    render_empty_state,
    render_kpi_card,
    render_page_header,
    render_section_header,
    render_status_badge,
)


def _get_portfolio_kpis() -> Dict[str, Any]:
    """Fetch portfolio KPI metrics from Supabase."""
    user_id = require_current_user_id()
    client = get_supabase_client()

    props = client.table("properties").select("COUNT", count="exact").eq("user_id", user_id).execute()
    total_properties = props.count or 0

    audits = client.table("audits").select("COUNT", count="exact").eq("user_id", user_id).execute()
    total_audits = audits.count or 0

    findings = client.table("findings").select("COUNT", count="exact").eq("user_id", user_id).execute()
    total_findings = findings.count or 0

    finding_rows = client.table("findings").select("amount").eq("user_id", user_id).execute()
    potential_recovery = sum(float(f.get("amount", 0)) for f in (finding_rows.data or []))

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
    """Fetch portfolio risk summary metrics."""
    user_id = require_current_user_id()
    client = get_supabase_client()

    risk_scores = client.table("risk_scores").select("overall_score, risk_level").eq("user_id", user_id).execute()
    scores = [float(r.get("overall_score", 0)) for r in (risk_scores.data or [])]
    overall_score = sum(scores) / len(scores) if scores else 0.0

    level_counts = {"critical": 0, "high": 0, "moderate": 0, "low": 0}
    for r in risk_scores.data or []:
        level = (r.get("risk_level") or "low").lower()
        if level in level_counts:
            level_counts[level] += 1

    high_risk_props = (
        client.table("risk_scores")
        .select("COUNT", count="exact")
        .eq("user_id", user_id)
        .gte("overall_score", 60)
        .execute()
    )
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
    """Fetch recovery status tracking by stage."""
    user_id = require_current_user_id()
    client = get_supabase_client()

    recovery_rows = client.table("recovery_records").select("status, amount").eq("user_id", user_id).execute()
    records = recovery_rows.data or []

    stages = {"Detected": 0.0, "Disputed": 0.0, "Under Review": 0.0, "Recovered": 0.0, "Rejected": 0.0}
    for r in records:
        status = r.get("status", "Detected")
        amt = float(r.get("amount", 0.0))
        if status in stages:
            stages[status] += amt
        else:
            stages[status] = amt

    return {
        "potential": sum(stages.values()),
        "detected": stages.get("Detected", 0.0),
        "disputed": stages.get("Disputed", 0.0),
        "under_review": stages.get("Under Review", 0.0),
        "recovered": stages.get("Recovered", 0.0),
        "rejected": stages.get("Rejected", 0.0),
    }


def _get_findings_by_category() -> pd.DataFrame:
    """Fetch findings grouped by category."""
    user_id = require_current_user_id()
    client = get_supabase_client()

    findings = client.table("findings").select("category, amount").eq("user_id", user_id).execute()
    categories: Dict[str, int] = {}
    for f in findings.data or []:
        cat = f.get("category", "Other")
        categories[cat] = categories.get(cat, 0) + 1

    return pd.DataFrame({"Category": list(categories.keys()), "Count": list(categories.values())})


def _get_high_risk_properties() -> pd.DataFrame:
    """Fetch high-risk properties with findings and recovery potential."""
    user_id = require_current_user_id()
    client = get_supabase_client()

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
        prop = client.table("properties").select("name, city, state").eq("id", prop_id).execute()
        prop_info = (prop.data or [{}])[0]
        prop_name = prop_info.get("name", "Unknown Property")
        location = f"{prop_info.get('city', '')}, {prop_info.get('state', '')}".strip(", ")

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
                "Location": location or "—",
                "Risk Score": f"{risk.get('overall_score', 0):.0f} / 100",
                "Risk Level": risk.get("risk_level", "Moderate").upper(),
                "Discrepancies": finding_count,
                "Potential Recovery": format_currency(recovery_amount),
            }
        )

    return pd.DataFrame(rows)


def _get_recent_findings() -> list:
    """Fetch recent findings with full metadata."""
    user_id = require_current_user_id()
    client = get_supabase_client()

    findings = (
        client.table("findings")
        .select("id, property_id, category, title, description, severity, amount, status, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(6)
        .execute()
    )

    result = []
    for f in findings.data or []:
        prop_id = f.get("property_id")
        prop = client.table("properties").select("name").eq("id", prop_id).execute()
        prop_name = (prop.data or [{}])[0].get("name", "Property") if prop.data else "Property"
        result.append({**f, "property_name": prop_name})
    return result


def _create_recovery_timeline_chart(recovery_tracking: Dict[str, Any]):
    """Create recovery pipeline status bar chart with light enterprise styling."""
    stages = ["Detected", "Disputed", "Under Review", "Recovered"]
    values = [
        recovery_tracking.get("detected", 0.0),
        recovery_tracking.get("disputed", 0.0),
        recovery_tracking.get("under_review", 0.0),
        recovery_tracking.get("recovered", 0.0),
    ]

    colors = [
        get_color("accent_blue"),
        get_color("accent_orange"),
        get_color("brand_teal"),
        get_color("success"),
    ]

    fig = go.Figure(
        data=[
            go.Bar(
                x=stages,
                y=values,
                marker=dict(color=colors, line=dict(color="rgba(0,0,0,0.05)", width=1)),
                text=[format_currency(v) if v > 0 else "$0" for v in values],
                textposition="outside",
                cliponaxis=False,
            )
        ]
    )

    layout = get_plotly_layout_theme()
    layout.update(
        title=dict(text="Recovery Pipeline Value by Stage", font=dict(size=14, color="#172033")),
        xaxis_title="Pipeline Stage",
        yaxis_title="Amount ($)",
        height=320,
    )
    fig.update_layout(layout)
    return fig


def _create_findings_chart(df: pd.DataFrame):
    """Create findings by category donut chart with light styling."""
    palette = [
        get_color("accent_blue"),
        get_color("brand_teal"),
        get_color("warning"),
        get_color("danger"),
        "#6366F1",
        "#8B5CF6",
    ]

    fig = px.pie(
        df,
        values="Count",
        names="Category",
        hole=0.55,
        color_discrete_sequence=palette,
    )

    layout = get_plotly_layout_theme()
    layout.update(
        title=dict(text="Discrepancies by Lease Category", font=dict(size=14, color="#172033")),
        height=320,
        showlegend=True,
    )
    fig.update_layout(layout)
    fig.update_traces(textinfo="percent+label", hoverinfo="label+value+percent")
    return fig


def render():
    """Render the main enterprise dashboard."""
    render_page_header(
        title="Portfolio Intelligence",
        subtitle="Portfolio intelligence, lease discrepancy detection, and financial recovery overview.",
        icon="◈",
    )

    # Fetch Data
    kpis = _get_portfolio_kpis()
    risk = _get_portfolio_risk()
    recovery = _get_recovery_tracking()

    # -----------------------------------------------------------------------
    # Top KPI Row (5 Pillars)
    # -----------------------------------------------------------------------
    render_section_header("Portfolio Overview", "Key operational compliance metrics across your active properties")

    kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)

    with kpi_col1:
        render_kpi_card(
            label="Total Properties",
            value=str(kpis["total_properties"]),
            context="Monitored portfolios",
            icon="🏢",
            accent_color=get_color("brand_blue"),
        )

    with kpi_col2:
        render_kpi_card(
            label="Active Audits",
            value=str(kpis["total_audits"]),
            context="Reconciliation sessions",
            icon="🔎",
            accent_color=get_color("brand_teal"),
        )

    with kpi_col3:
        render_kpi_card(
            label="Potential Recovery",
            value=format_currency(kpis["potential_recovery"]),
            context=f"{kpis['total_findings']} flagged findings",
            icon="💰",
            accent_color=get_color("warning"),
        )

    with kpi_col4:
        render_kpi_card(
            label="Recovered Amount",
            value=format_currency(kpis["recovered_amount"]),
            context="Funds recaptured",
            icon="✅",
            accent_color=get_color("success"),
        )

    with kpi_col5:
        risk_score = risk["overall_score"]
        risk_color = (
            get_color("risk_critical") if risk_score >= 70
            else get_color("risk_high") if risk_score >= 50
            else get_color("risk_moderate") if risk_score >= 30
            else get_color("risk_low")
        )
        risk_label = (
            "Critical" if risk_score >= 70
            else "High" if risk_score >= 50
            else "Moderate" if risk_score >= 30
            else "Low Risk"
        )
        render_kpi_card(
            label="Portfolio Risk",
            value=f"{risk_score:.0f} / 100",
            context=f"● {risk_label}",
            icon="📊",
            accent_color=risk_color,
        )

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # Charts Row: Recovery Pipeline + Findings by Category
    # -----------------------------------------------------------------------
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        fig_recovery = _create_recovery_timeline_chart(recovery)
        st.plotly_chart(fig_recovery, use_container_width=True)

    with col_chart2:
        df_findings = _get_findings_by_category()
        if not df_findings.empty:
            fig_findings = _create_findings_chart(df_findings)
            st.plotly_chart(fig_findings, use_container_width=True)
        else:
            render_empty_state(
                title="No Categorized Findings",
                description="Run deterministic lease audits against your invoice statements to populate category breakdown charts.",
                icon="📊",
            )

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # High-Risk Properties & Action Items
    # -----------------------------------------------------------------------
    render_section_header("High-Risk Properties", "Properties exceeding contract compliance thresholds")

    df_high_risk = _get_high_risk_properties()
    if not df_high_risk.empty:
        st.dataframe(
            df_high_risk,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Risk Score": st.column_config.TextColumn("Risk Score", help="Normalized score 0-100"),
                "Risk Level": st.column_config.TextColumn("Risk Level"),
                "Potential Recovery": st.column_config.TextColumn("Potential Recovery"),
            }
        )
    else:
        render_empty_state(
            title="No High-Risk Properties Flagged",
            description="All active properties are within acceptable risk parameters or awaiting audit.",
            icon="🛡️",
        )

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # Recent Findings
    # -----------------------------------------------------------------------
    render_section_header("Recent Audit Discrepancies", "Latest contract discrepancies detected across recent invoices")

    recent_findings = _get_recent_findings()
    if recent_findings:
        for f in recent_findings:
            sev = (f.get("severity") or "low").lower()
            badge = render_status_badge(sev)
            amt = float(f.get("amount", 0.0))
            prop_name = f.get("property_name", "Property")
            cat = f.get("category", "Lease Finding")

            with st.container(border=True):
                c1, c2, c3 = st.columns([2.5, 1.2, 1])
                with c1:
                    st.markdown(
                        f"""
                        <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.25rem;">
                            {badge}
                            <span style="font-size:0.75rem; font-weight:700; color:#64748B; text-transform:uppercase;">
                                {cat}
                            </span>
                            <span style="font-size:0.8125rem; color:#94A3B8;">• {prop_name}</span>
                        </div>
                        <div style="font-size:0.9375rem; font-weight:700; color:#172033;">
                            {f.get('title', 'Discrepancy')}
                        </div>
                        <div style="font-size:0.8125rem; color:#667085; margin-top:0.125rem;">
                            {f.get('description', '')}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with c2:
                    st.markdown(
                        f"""
                        <div style="text-align:right;">
                            <span style="font-size:0.6875rem; font-weight:700; color:#64748B; text-transform:uppercase;">
                                Discrepancy
                            </span>
                            <div style="font-size:1.125rem; font-weight:800; color:#16A34A;">
                                {format_currency(amt)}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with c3:
                    status_badge = render_status_badge(f.get("status", "open"))
                    st.markdown(
                        f"""
                        <div style="text-align:right;">
                            <span style="font-size:0.6875rem; font-weight:700; color:#64748B; text-transform:uppercase; display:block; margin-bottom:0.2rem;">
                                Status
                            </span>
                            {status_badge}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
    else:
        render_empty_state(
            title="No Recent Audit Discrepancies",
            description="Completed audits with invoice overcharges and non-compliance will appear here.",
            icon="🔎",
        )
