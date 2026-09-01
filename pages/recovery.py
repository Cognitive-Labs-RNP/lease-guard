"""
Recovery page for LeaseGuard.

Track and manage recovery pipeline and status.
"""

from typing import Any, Dict

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.auth import get_supabase_client, require_current_user_id
from ui.custom_theme import get_color


def _get_recovery_records() -> list[Dict[str, Any]]:
    """Fetch all recovery records."""
    user_id = require_current_user_id()
    client = get_supabase_client()

    response = client.table("recovery_records").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return response.data or []


def _get_properties() -> list[Dict[str, Any]]:
    """Fetch user's properties."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("properties").select("id, name").eq("user_id", user_id).order("name").execute()
    return response.data or []


def _update_recovery_status(recovery_id: str, new_status: str, notes: str = ""):
    """Update recovery record status."""
    client = get_supabase_client()

    update_data = {"status": new_status}
    if notes:
        update_data["notes"] = notes

    client.table("recovery_records").update(update_data).eq("id", recovery_id).execute()


def _create_recovery_pipeline_chart(recovery_data: list[Dict[str, Any]]):
    """Create Sankey diagram of recovery pipeline."""
    # Count by status
    status_counts = {}
    for rec in recovery_data:
        status = rec.get("status", "Detected")
        status_counts[status] = status_counts.get(status, 0) + 1

    statuses = ["Detected", "Disputed", "Under Review", "Recovered", "Rejected"]
    counts = [status_counts.get(s, 0) for s in statuses]

    fig = go.Figure(
        data=[
            go.Bar(
                x=statuses,
                y=counts,
                marker=dict(
                    color=[
                        get_color("accent_blue"),
                        get_color("accent_orange"),
                        get_color("accent_yellow"),
                        get_color("accent_green"),
                        get_color("risk_critical"),
                    ]
                ),
                text=counts,
                textposition="auto",
            )
        ]
    )

    fig.update_layout(
        title="Recovery Pipeline Status",
        xaxis_title="Status",
        yaxis_title="Count",
        template="plotly_dark",
        plot_bgcolor=get_color("bg_secondary"),
        paper_bgcolor=get_color("bg_secondary"),
        font=dict(color=get_color("text_primary")),
        showlegend=False,
    )

    return fig


def render():
    """Render the recovery page."""
    st.markdown("## 💰 Recovery")

    recovery_data = _get_recovery_records()
    properties = _get_properties()
    prop_dict = {p["id"]: p["name"] for p in properties}

    if not recovery_data:
        st.info("No recovery records yet. Run audits to generate recovery items.")
        return

    # Summary metrics
    st.markdown("### Recovery Summary")

    col1, col2, col3, col4, col5 = st.columns(5)

    detected = sum(float(r.get("amount", 0)) for r in recovery_data if r.get("status") == "Detected")
    disputed = sum(float(r.get("amount", 0)) for r in recovery_data if r.get("status") == "Disputed")
    under_review = sum(float(r.get("amount", 0)) for r in recovery_data if r.get("status") == "Under Review")
    recovered = sum(float(r.get("amount", 0)) for r in recovery_data if r.get("status") == "Recovered")
    rejected = sum(float(r.get("amount", 0)) for r in recovery_data if r.get("status") == "Rejected")

    with col1:
        st.metric("Detected", f"${detected:,.2f}")

    with col2:
        st.metric("Disputed", f"${disputed:,.2f}")

    with col3:
        st.metric("Under Review", f"${under_review:,.2f}")

    with col4:
        st.metric("Recovered", f"${recovered:,.2f}")

    with col5:
        st.metric("Rejected", f"${rejected:,.2f}")

    # Chart
    fig = _create_recovery_pipeline_chart(recovery_data)
    st.plotly_chart(fig, use_container_width=True)

    # Recovery details by status
    st.markdown("---")
    st.markdown("### Recovery Items by Status")

    status_filter = st.selectbox(
        "Filter by Status",
        ["All", "Detected", "Disputed", "Under Review", "Recovered", "Rejected"],
        key="recovery_status_filter"
    )

    # Filter data
    filtered_data = recovery_data
    if status_filter != "All":
        filtered_data = [r for r in recovery_data if r.get("status") == status_filter]

    if filtered_data:
        st.markdown(f"**{len(filtered_data)} recovery items**")

        for recovery in filtered_data:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                prop_name = prop_dict.get(recovery.get("property_id"), "Unknown")

                with col1:
                    st.write(f"**Property**: {prop_name}")
                    st.write(f"**Amount**: ${float(recovery.get('amount', 0)):,.2f}")

                with col2:
                    st.write(f"**Status**: {recovery.get('status', 'N/A')}")
                    st.write(f"**Created**: {recovery.get('created_at', 'N/A')[:10]}")

                with col3:
                    if recovery.get("notes"):
                        st.write(f"**Notes**: {recovery['notes'][:50]}...")

                with col4:
                    # Status update buttons
                    current_status = recovery.get("status", "Detected")

                    if current_status == "Detected":
                        if st.button("Dispute", key=f"dispute_{recovery['id']}"):
                            _update_recovery_status(recovery["id"], "Disputed", "Marked as disputed")
                            st.success("Updated to Disputed")
                            st.rerun()

                    elif current_status == "Disputed":
                        if st.button("Review", key=f"review_{recovery['id']}"):
                            _update_recovery_status(recovery["id"], "Under Review", "Submitted for review")
                            st.success("Updated to Under Review")
                            st.rerun()

                    elif current_status == "Under Review":
                        col4a, col4b = st.columns(2)
                        with col4a:
                            if st.button("Recover", key=f"recover_{recovery['id']}", type="primary"):
                                _update_recovery_status(recovery["id"], "Recovered", "Amount recovered")
                                st.success("Marked as Recovered")
                                st.rerun()
                        with col4b:
                            if st.button("Reject", key=f"reject_{recovery['id']}"):
                                _update_recovery_status(recovery["id"], "Rejected", "Recovery rejected")
                                st.success("Marked as Rejected")
                                st.rerun()

    else:
        st.info(f"No recovery items with status '{status_filter}'")
