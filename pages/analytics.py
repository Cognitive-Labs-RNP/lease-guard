"""
Analytics page for LeaseGuard.

Historical and comparative analytics across portfolio.
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


def _get_audits() -> list[Dict[str, Any]]:
    """Fetch all audits."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("audits").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return response.data or []


def _get_findings() -> list[Dict[str, Any]]:
    """Fetch all findings."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("findings").select("*").eq("user_id", user_id).execute()
    return response.data or []


def _get_recovery_records() -> list[Dict[str, Any]]:
    """Fetch all recovery records."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("recovery_records").select("*").eq("user_id", user_id).execute()
    return response.data or []


def _get_properties() -> list[Dict[str, Any]]:
    """Fetch user's properties."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("properties").select("id, name").eq("user_id", user_id).order("name").execute()
    return response.data or []


def render():
    """Render the analytics page."""
    st.markdown("## 📈 Analytics")

    tab1, tab2 = st.tabs(["Historical Trends", "Property Comparison"])

    with tab1:
        st.markdown("### Historical Analysis")

        properties = _get_properties()
        prop_dict = {p["id"]: p["name"] for p in properties}

        if not properties:
            st.info("No properties yet")
            return

        # Property selector
        selected_prop_name = st.selectbox(
            "Select Property",
            options=["All"] + [p["name"] for p in properties],
            key="historical_prop_select"
        )

        # Metric selector
        metric = st.selectbox(
            "Select Metric",
            ["Risk Score", "Findings Count", "Potential Recovery", "Recovered Amount"],
            key="historical_metric_select"
        )

        # Date range
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", key="hist_start_date")
        with col2:
            end_date = st.date_input("End Date", key="hist_end_date")

        # Build data for chart
        if metric == "Risk Score":
            risk_scores = _get_risk_scores()

            # Filter by property if selected
            if selected_prop_name != "All":
                selected_prop_id = next((p["id"] for p in properties if p["name"] == selected_prop_name), None)
                risk_scores = [r for r in risk_scores if r.get("property_id") == selected_prop_id]

            if risk_scores:
                # Create time series data
                df = pd.DataFrame([
                    {
                        "Date": r.get("calculated_at", "")[:10],
                        "Risk Score": r.get("overall_score", 0),
                        "Property": prop_dict.get(r.get("property_id"), "Unknown"),
                    }
                    for r in risk_scores
                ])

                if selected_prop_name == "All":
                    fig = px.line(
                        df,
                        x="Date",
                        y="Risk Score",
                        color="Property",
                        title="Risk Score Over Time",
                        markers=True
                    )
                else:
                    fig = px.line(
                        df,
                        x="Date",
                        y="Risk Score",
                        title=f"Risk Score for {selected_prop_name}",
                        markers=True
                    )

                fig.update_layout(
                    template="plotly_dark",
                    plot_bgcolor=get_color("bg_secondary"),
                    paper_bgcolor=get_color("bg_secondary"),
                    font=dict(color=get_color("text_primary")),
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No risk score data available")

        elif metric == "Findings Count":
            findings = _get_findings()

            # Group by date and property
            data = []
            for finding in findings:
                date = finding.get("created_at", "")[:10]
                prop_id = finding.get("property_id")
                prop_name = prop_dict.get(prop_id, "Unknown")

                if selected_prop_name == "All" or prop_name == selected_prop_name:
                    data.append({"Date": date, "Count": 1, "Property": prop_name})

            if data:
                df = pd.DataFrame(data)
                df = df.groupby(["Date", "Property"]).size().reset_index(name="Count")

                if selected_prop_name == "All":
                    fig = px.bar(
                        df,
                        x="Date",
                        y="Count",
                        color="Property",
                        title="Findings Over Time",
                    )
                else:
                    fig = px.bar(
                        df,
                        x="Date",
                        y="Count",
                        title=f"Findings for {selected_prop_name}",
                    )

                fig.update_layout(
                    template="plotly_dark",
                    plot_bgcolor=get_color("bg_secondary"),
                    paper_bgcolor=get_color("bg_secondary"),
                    font=dict(color=get_color("text_primary")),
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No findings data")

        elif metric == "Potential Recovery":
            findings = _get_findings()

            # Group by date
            data = []
            for finding in findings:
                date = finding.get("created_at", "")[:10]
                prop_id = finding.get("property_id")
                prop_name = prop_dict.get(prop_id, "Unknown")
                amount = float(finding.get("amount", 0))

                if selected_prop_name == "All" or prop_name == selected_prop_name:
                    data.append({"Date": date, "Amount": amount, "Property": prop_name})

            if data:
                df = pd.DataFrame(data)
                df = df.groupby(["Date", "Property"])["Amount"].sum().reset_index()

                if selected_prop_name == "All":
                    fig = px.line(
                        df,
                        x="Date",
                        y="Amount",
                        color="Property",
                        title="Potential Recovery Over Time",
                        markers=True
                    )
                else:
                    fig = px.line(
                        df,
                        x="Date",
                        y="Amount",
                        title=f"Potential Recovery for {selected_prop_name}",
                        markers=True
                    )

                fig.update_layout(
                    template="plotly_dark",
                    plot_bgcolor=get_color("bg_secondary"),
                    paper_bgcolor=get_color("bg_secondary"),
                    font=dict(color=get_color("text_primary")),
                    yaxis_title="Amount ($)",
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No recovery data")

        else:  # Recovered Amount
            recovery = _get_recovery_records()

            # Filter for recovered status
            recovery = [r for r in recovery if r.get("status") == "Recovered"]

            # Group by date
            data = []
            for rec in recovery:
                date = rec.get("created_at", "")[:10]
                prop_id = rec.get("property_id")
                prop_name = prop_dict.get(prop_id, "Unknown")
                amount = float(rec.get("amount", 0))

                if selected_prop_name == "All" or prop_name == selected_prop_name:
                    data.append({"Date": date, "Amount": amount, "Property": prop_name})

            if data:
                df = pd.DataFrame(data)
                df = df.groupby(["Date", "Property"])["Amount"].sum().reset_index()

                if selected_prop_name == "All":
                    fig = px.line(
                        df,
                        x="Date",
                        y="Amount",
                        color="Property",
                        title="Recovered Amount Over Time",
                        markers=True
                    )
                else:
                    fig = px.line(
                        df,
                        x="Date",
                        y="Amount",
                        title=f"Recovered Amount for {selected_prop_name}",
                        markers=True
                    )

                fig.update_layout(
                    template="plotly_dark",
                    plot_bgcolor=get_color("bg_secondary"),
                    paper_bgcolor=get_color("bg_secondary"),
                    font=dict(color=get_color("text_primary")),
                    yaxis_title="Amount ($)",
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No recovered amounts yet")

    with tab2:
        st.markdown("### Property Comparison")

        properties = _get_properties()

        if len(properties) < 2:
            st.info("Need at least 2 properties to compare")
            return

        prop_names = [p["name"] for p in properties]
        prop_dict = {p["id"]: p["name"] for p in properties}

        # Multi-select properties
        selected_props = st.multiselect(
            "Select Properties to Compare",
            prop_names,
            default=prop_names[:2],
            key="compare_props_select"
        )

        if not selected_props:
            st.info("Select at least one property")
            return

        # Metric selector
        metric = st.selectbox(
            "Comparison Metric",
            ["Risk Score", "Findings Count", "Potential Recovery", "Recovered Amount"],
            key="compare_metric_select"
        )

        # Build comparison data
        selected_prop_ids = [p["id"] for p in properties if p["name"] in selected_props]

        if metric == "Risk Score":
            risk_scores = _get_risk_scores()
            risk_scores = [r for r in risk_scores if r.get("property_id") in selected_prop_ids]

            data = []
            for score in risk_scores:
                prop_name = prop_dict.get(score.get("property_id"), "Unknown")
                data.append({
                    "Property": prop_name,
                    "Risk Score": score.get("overall_score", 0),
                })

            if data:
                df = pd.DataFrame(data)
                fig = px.bar(
                    df,
                    x="Property",
                    y="Risk Score",
                    title="Risk Score Comparison",
                    color="Risk Score",
                    color_continuous_scale="RdYlGn_r"
                )

                fig.update_layout(
                    template="plotly_dark",
                    plot_bgcolor=get_color("bg_secondary"),
                    paper_bgcolor=get_color("bg_secondary"),
                    font=dict(color=get_color("text_primary")),
                )

                st.plotly_chart(fig, use_container_width=True)

        elif metric == "Findings Count":
            findings = _get_findings()
            findings = [f for f in findings if f.get("property_id") in selected_prop_ids]

            data = []
            for prop_id in selected_prop_ids:
                prop_name = prop_dict.get(prop_id, "Unknown")
                count = sum(1 for f in findings if f.get("property_id") == prop_id)
                data.append({"Property": prop_name, "Findings": count})

            if data:
                df = pd.DataFrame(data)
                fig = px.bar(
                    df,
                    x="Property",
                    y="Findings",
                    title="Findings Count Comparison",
                    color="Findings",
                    color_continuous_scale="Viridis"
                )

                fig.update_layout(
                    template="plotly_dark",
                    plot_bgcolor=get_color("bg_secondary"),
                    paper_bgcolor=get_color("bg_secondary"),
                    font=dict(color=get_color("text_primary")),
                )

                st.plotly_chart(fig, use_container_width=True)

        elif metric == "Potential Recovery":
            findings = _get_findings()
            findings = [f for f in findings if f.get("property_id") in selected_prop_ids]

            data = []
            for prop_id in selected_prop_ids:
                prop_name = prop_dict.get(prop_id, "Unknown")
                total = sum(float(f.get("amount", 0)) for f in findings if f.get("property_id") == prop_id)
                data.append({"Property": prop_name, "Recovery": total})

            if data:
                df = pd.DataFrame(data)
                fig = px.bar(
                    df,
                    x="Property",
                    y="Recovery",
                    title="Potential Recovery Comparison",
                    color="Recovery",
                    color_continuous_scale="Greens"
                )

                fig.update_layout(
                    template="plotly_dark",
                    plot_bgcolor=get_color("bg_secondary"),
                    paper_bgcolor=get_color("bg_secondary"),
                    font=dict(color=get_color("text_primary")),
                    yaxis_title="Amount ($)",
                )

                st.plotly_chart(fig, use_container_width=True)

        else:  # Recovered Amount
            recovery = _get_recovery_records()
            recovery = [r for r in recovery if r.get("property_id") in selected_prop_ids and r.get("status") == "Recovered"]

            data = []
            for prop_id in selected_prop_ids:
                prop_name = prop_dict.get(prop_id, "Unknown")
                total = sum(float(r.get("amount", 0)) for r in recovery if r.get("property_id") == prop_id)
                data.append({"Property": prop_name, "Recovered": total})

            if data:
                df = pd.DataFrame(data)
                fig = px.bar(
                    df,
                    x="Property",
                    y="Recovered",
                    title="Recovered Amount Comparison",
                    color="Recovered",
                    color_continuous_scale="Blues"
                )

                fig.update_layout(
                    template="plotly_dark",
                    plot_bgcolor=get_color("bg_secondary"),
                    paper_bgcolor=get_color("bg_secondary"),
                    font=dict(color=get_color("text_primary")),
                    yaxis_title="Amount ($)",
                )

                st.plotly_chart(fig, use_container_width=True)
