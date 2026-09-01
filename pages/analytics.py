"""
Analytics page for LeaseGuard AI.

Historical and comparative multi-property analytics across risk, discrepancies,
and capital recoveries.
"""

from typing import Any, Dict, List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from services.auth import get_supabase_client, require_current_user_id
from ui.custom_theme import COLORS, get_color, get_plotly_layout_theme
from utils.ui import (
    format_currency,
    render_divider,
    render_empty_state,
    render_page_header,
    render_section_header,
)


def _get_risk_scores() -> List[Dict[str, Any]]:
    """Fetch all risk scores."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("risk_scores").select("*").eq("user_id", user_id).order("calculated_at", desc=True).execute()
    return response.data or []


def _get_audits() -> List[Dict[str, Any]]:
    """Fetch all audits."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("audits").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return response.data or []


def _get_findings() -> List[Dict[str, Any]]:
    """Fetch all findings."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("findings").select("*").eq("user_id", user_id).execute()
    return response.data or []


def _get_recovery_records() -> List[Dict[str, Any]]:
    """Fetch all recovery records."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("recovery_records").select("*").eq("user_id", user_id).execute()
    return response.data or []


def _get_properties() -> List[Dict[str, Any]]:
    """Fetch user's properties."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("properties").select("id, name").eq("user_id", user_id).order("name").execute()
    return response.data or []


def render():
    """Render the enterprise analytics and multi-property comparison dashboard."""
    render_page_header(
        title="Portfolio Analytics",
        subtitle="Analyze longitudinal compliance trends, multi-property risk correlations, and capital recovery rates.",
        icon="📈",
    )

    properties = _get_properties()
    if not properties:
        render_empty_state(
            title="No Portfolio Assets Available",
            description="Add properties and run audits to generate comparative analytics.",
            icon="📈",
        )
        return

    prop_dict = {p["id"]: p["name"] for p in properties}
    prop_names = [p["name"] for p in properties]

    tab_hist, tab_comp = st.tabs(["Longitudinal Trends", "Multi-Property Comparison"])

    # -----------------------------------------------------------------------
    # TAB 1: HISTORICAL TRENDS
    # -----------------------------------------------------------------------
    with tab_hist:
        render_section_header("Historical Metric Analysis", "Select properties and dimensions to observe historical behavior")

        c1, c2 = st.columns(2)
        with c1:
            selected_prop_name = st.selectbox(
                "Filter by Property",
                options=["All Properties"] + prop_names,
                key="hist_prop_analytics_select",
            )
        with c2:
            metric = st.selectbox(
                "Compliance Dimension",
                ["Risk Score Trend", "Discrepancy Volume", "Potential Recovery ($)", "Recovered Capital ($)"],
                key="hist_metric_analytics_select",
            )

        # 1. Risk Score Trend
        if metric == "Risk Score Trend":
            risk_scores = _get_risk_scores()
            if selected_prop_name != "All Properties":
                sel_id = next((p["id"] for p in properties if p["name"] == selected_prop_name), None)
                risk_scores = [r for r in risk_scores if r.get("property_id") == sel_id]

            if risk_scores:
                df = pd.DataFrame([
                    {
                        "Date": r.get("calculated_at", "")[:10],
                        "Risk Score": float(r.get("overall_score", 0)),
                        "Property": prop_dict.get(r.get("property_id"), "Property"),
                    }
                    for r in risk_scores
                ])

                fig = px.line(
                    df,
                    x="Date",
                    y="Risk Score",
                    color="Property" if selected_prop_name == "All Properties" else None,
                    title=f"Risk Score Trajectory ({selected_prop_name})",
                    markers=True,
                    color_discrete_sequence=[get_color("brand_blue"), get_color("brand_teal"), get_color("warning")],
                )
                layout = get_plotly_layout_theme()
                layout.update(height=380, yaxis_range=[0, 100])
                fig.update_layout(layout)
                st.plotly_chart(fig, use_container_width=True)
            else:
                render_empty_state("No Risk History Available", "No calculated risk points recorded for this selection.", "📊")

        # 2. Discrepancy Volume
        elif metric == "Discrepancy Volume":
            findings = _get_findings()
            data = []
            for f in findings:
                p_name = prop_dict.get(f.get("property_id"), "Property")
                if selected_prop_name == "All Properties" or p_name == selected_prop_name:
                    data.append({
                        "Date": f.get("created_at", "")[:10],
                        "Property": p_name,
                    })

            if data:
                df = pd.DataFrame(data)
                df_grouped = df.groupby(["Date", "Property"]).size().reset_index(name="Findings Count")

                fig = px.bar(
                    df_grouped,
                    x="Date",
                    y="Findings Count",
                    color="Property" if selected_prop_name == "All Properties" else None,
                    title=f"Discrepancies Identified by Date ({selected_prop_name})",
                    color_discrete_sequence=[get_color("brand_blue"), get_color("brand_teal"), get_color("warning")],
                )
                layout = get_plotly_layout_theme()
                layout.update(height=380)
                fig.update_layout(layout)
                st.plotly_chart(fig, use_container_width=True)
            else:
                render_empty_state("No Finding Logs", "No discrepancy logs found for selected criteria.", "🔎")

        # 3. Potential Recovery
        elif metric == "Potential Recovery ($)":
            findings = _get_findings()
            data = []
            for f in findings:
                p_name = prop_dict.get(f.get("property_id"), "Property")
                amt = float(f.get("amount", 0.0))
                if selected_prop_name == "All Properties" or p_name == selected_prop_name:
                    data.append({
                        "Date": f.get("created_at", "")[:10],
                        "Amount": amt,
                        "Property": p_name,
                    })

            if data:
                df = pd.DataFrame(data)
                df_grouped = df.groupby(["Date", "Property"])["Amount"].sum().reset_index()

                fig = px.line(
                    df_grouped,
                    x="Date",
                    y="Amount",
                    color="Property" if selected_prop_name == "All Properties" else None,
                    title=f"Potential Recovery Value Identified ({selected_prop_name})",
                    markers=True,
                    color_discrete_sequence=[get_color("warning"), get_color("brand_blue"), get_color("brand_teal")],
                )
                layout = get_plotly_layout_theme()
                layout.update(height=380, yaxis_title="Amount ($)")
                fig.update_layout(layout)
                st.plotly_chart(fig, use_container_width=True)
            else:
                render_empty_state("No Recovery Potential Data", "No financial recovery amounts identified yet.", "💰")

        # 4. Recovered Capital
        else:
            recovery = _get_recovery_records()
            rec_recovered = [r for r in recovery if r.get("status") == "Recovered"]
            data = []
            for r in rec_recovered:
                p_name = prop_dict.get(r.get("property_id"), "Property")
                amt = float(r.get("amount", 0.0))
                if selected_prop_name == "All Properties" or p_name == selected_prop_name:
                    data.append({
                        "Date": r.get("created_at", "")[:10],
                        "Amount": amt,
                        "Property": p_name,
                    })

            if data:
                df = pd.DataFrame(data)
                df_grouped = df.groupby(["Date", "Property"])["Amount"].sum().reset_index()

                fig = px.bar(
                    df_grouped,
                    x="Date",
                    y="Amount",
                    color="Property" if selected_prop_name == "All Properties" else None,
                    title=f"Capital Successfully Recovered ({selected_prop_name})",
                    color_discrete_sequence=[get_color("success"), get_color("brand_blue")],
                )
                layout = get_plotly_layout_theme()
                layout.update(height=380, yaxis_title="Recovered ($)")
                fig.update_layout(layout)
                st.plotly_chart(fig, use_container_width=True)
            else:
                render_empty_state("No Recoveries Finalized", "Mark disputed items as 'Recovered' to populate this metric.", "✅")

    # -----------------------------------------------------------------------
    # TAB 2: MULTI-PROPERTY COMPARISON
    # -----------------------------------------------------------------------
    with tab_comp:
        render_section_header("Cross-Property Benchmark Matrix", "Compare key metrics across selected commercial properties")

        selected_compare_props = st.multiselect(
            "Select Properties to Benchmark",
            prop_names,
            default=prop_names[:min(4, len(prop_names))],
            key="comp_multiselect",
        )

        if not selected_compare_props:
            render_empty_state("Select Properties", "Choose at least one property to view the benchmark comparison.", "🏢")
            return

        comp_metric = st.selectbox(
            "Benchmark Dimension",
            ["Risk Score (Average)", "Total Discrepancies Flagged", "Total Potential Recovery ($)", "Total Recovered Capital ($)"],
            key="comp_dim_select",
        )

        selected_ids = [p["id"] for p in properties if p["name"] in selected_compare_props]

        if comp_metric == "Risk Score (Average)":
            risk_scores = _get_risk_scores()
            data = []
            for p_id in selected_ids:
                p_scores = [float(r.get("overall_score", 0)) for r in risk_scores if r.get("property_id") == p_id]
                avg = sum(p_scores) / len(p_scores) if p_scores else 0.0
                data.append({"Property": prop_dict.get(p_id, "Property"), "Average Risk Score": round(avg, 1)})

            df_comp = pd.DataFrame(data)
            fig = px.bar(
                df_comp,
                x="Property",
                y="Average Risk Score",
                color="Average Risk Score",
                color_continuous_scale=["#16A34A", "#D97706", "#DC2626"],
                title="Cross-Property Average Risk Index",
            )
            layout = get_plotly_layout_theme()
            layout.update(height=360, yaxis_range=[0, 100])
            fig.update_layout(layout)
            st.plotly_chart(fig, use_container_width=True)

        elif comp_metric == "Total Discrepancies Flagged":
            findings = _get_findings()
            data = []
            for p_id in selected_ids:
                cnt = sum(1 for f in findings if f.get("property_id") == p_id)
                data.append({"Property": prop_dict.get(p_id, "Property"), "Discrepancies": cnt})

            df_comp = pd.DataFrame(data)
            fig = px.bar(
                df_comp,
                x="Property",
                y="Discrepancies",
                title="Total Flagged Discrepancies per Asset",
                color_discrete_sequence=[get_color("brand_blue")],
            )
            layout = get_plotly_layout_theme()
            layout.update(height=360)
            fig.update_layout(layout)
            st.plotly_chart(fig, use_container_width=True)

        elif comp_metric == "Total Potential Recovery ($)":
            findings = _get_findings()
            data = []
            for p_id in selected_ids:
                tot = sum(float(f.get("amount", 0)) for f in findings if f.get("property_id") == p_id)
                data.append({"Property": prop_dict.get(p_id, "Property"), "Potential Recovery ($)": tot})

            df_comp = pd.DataFrame(data)
            fig = px.bar(
                df_comp,
                x="Property",
                y="Potential Recovery ($)",
                title="Total Overcharge Capital Identified ($)",
                color_discrete_sequence=[get_color("warning")],
                text=[format_currency(v) for v in df_comp["Potential Recovery ($)"]],
            )
            layout = get_plotly_layout_theme()
            layout.update(height=360)
            fig.update_layout(layout)
            st.plotly_chart(fig, use_container_width=True)

        else:
            recovery = _get_recovery_records()
            data = []
            for p_id in selected_ids:
                tot = sum(float(r.get("amount", 0)) for r in recovery if r.get("property_id") == p_id and r.get("status") == "Recovered")
                data.append({"Property": prop_dict.get(p_id, "Property"), "Recovered Amount ($)": tot})

            df_comp = pd.DataFrame(data)
            fig = px.bar(
                df_comp,
                x="Property",
                y="Recovered Amount ($)",
                title="Recaptured Capital per Asset ($)",
                color_discrete_sequence=[get_color("success")],
                text=[format_currency(v) for v in df_comp["Recovered Amount ($)"]],
            )
            layout = get_plotly_layout_theme()
            layout.update(height=360)
            fig.update_layout(layout)
            st.plotly_chart(fig, use_container_width=True)
