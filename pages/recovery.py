"""
Recovery page for LeaseGuard AI.

Track and manage the financial recovery lifecycle across detected overcharges,
formal disputes, reviews, and recaptured capital.
"""

from typing import Any, Dict, List
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.auth import get_supabase_client, require_current_user_id
from ui.custom_theme import COLORS, get_color, get_plotly_layout_theme
from utils.ui import (
    format_currency,
    render_alert,
    render_divider,
    render_empty_state,
    render_kpi_card,
    render_page_header,
    render_section_header,
    render_status_badge,
)


def _get_recovery_records() -> List[Dict[str, Any]]:
    """Fetch all recovery records."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("recovery_records").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return response.data or []


def _get_properties() -> List[Dict[str, Any]]:
    """Fetch user's properties."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("properties").select("id, name").eq("user_id", user_id).order("name").execute()
    return response.data or []


def _update_recovery_status(recovery_id: str, new_status: str, notes: str = ""):
    """Update recovery record status."""
    client = get_supabase_client()
    update_data: Dict[str, Any] = {"status": new_status}
    if notes:
        update_data["notes"] = notes
    client.table("recovery_records").update(update_data).eq("id", recovery_id).execute()


def _create_recovery_pipeline_chart(recovery_data: List[Dict[str, Any]]):
    """Create recovery pipeline status bar chart."""
    status_totals = {
        "Detected": 0.0,
        "Disputed": 0.0,
        "Under Review": 0.0,
        "Recovered": 0.0,
        "Rejected": 0.0,
    }

    for rec in recovery_data:
        st_name = rec.get("status", "Detected")
        amt = float(rec.get("amount", 0.0))
        if st_name in status_totals:
            status_totals[st_name] += amt

    statuses = list(status_totals.keys())
    values = list(status_totals.values())
    colors = [
        get_color("accent_blue"),
        get_color("warning"),
        get_color("brand_teal"),
        get_color("success"),
        get_color("danger"),
    ]

    fig = go.Figure(
        data=[
            go.Bar(
                x=statuses,
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
        title=dict(text="Total Financial Value by Recovery Stage", font=dict(size=14, color="#172033")),
        xaxis_title="Pipeline Stage",
        yaxis_title="Amount ($)",
        height=320,
    )
    fig.update_layout(layout)
    return fig


def render():
    """Render the recovery pipeline management interface."""
    render_page_header(
        title="Financial Recovery Pipeline",
        subtitle="Track overcharges from initial detection through formal dispute, audit review, and capital recovery.",
        icon="💰",
    )

    recovery_data = _get_recovery_records()
    properties = _get_properties()
    prop_dict = {p["id"]: p["name"] for p in properties}

    if not recovery_data:
        render_empty_state(
            title="No Recovery Items in Pipeline",
            description="Run deterministic lease audits against your invoice statements to detect overcharges and create recovery items.",
            icon="💰",
        )
        return

    # Calculate stage totals
    detected_sum = sum(float(r.get("amount", 0)) for r in recovery_data if r.get("status") == "Detected")
    disputed_sum = sum(float(r.get("amount", 0)) for r in recovery_data if r.get("status") == "Disputed")
    review_sum = sum(float(r.get("amount", 0)) for r in recovery_data if r.get("status") == "Under Review")
    recovered_sum = sum(float(r.get("amount", 0)) for r in recovery_data if r.get("status") == "Recovered")
    rejected_sum = sum(float(r.get("amount", 0)) for r in recovery_data if r.get("status") == "Rejected")
    total_pipeline = sum(float(r.get("amount", 0)) for r in recovery_data)

    # -----------------------------------------------------------------------
    # Connected Pipeline Header
    # -----------------------------------------------------------------------
    render_section_header("Pipeline Stage Overview", "Real-time summary of capital progressing through dispute stages")

    st.markdown(
        f"""
        <div class="pipeline-bar">
            <div class="pipeline-card" style="border-left: 4px solid #1D4ED8;">
                <div class="pipeline-card-label">01. Detected Overcharges</div>
                <div class="pipeline-card-value" style="color:#1D4ED8;">{format_currency(detected_sum)}</div>
            </div>
            <div class="pipeline-card" style="border-left: 4px solid #D97706;">
                <div class="pipeline-card-label">02. Formally Disputed</div>
                <div class="pipeline-card-value" style="color:#D97706;">{format_currency(disputed_sum)}</div>
            </div>
            <div class="pipeline-card" style="border-left: 4px solid #0891B2;">
                <div class="pipeline-card-label">03. Under Audit Review</div>
                <div class="pipeline-card-value" style="color:#0891B2;">{format_currency(review_sum)}</div>
            </div>
            <div class="pipeline-card" style="border-left: 4px solid #16A34A;">
                <div class="pipeline-card-label">04. Capital Recovered</div>
                <div class="pipeline-card-value" style="color:#16A34A;">{format_currency(recovered_sum)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Chart
    fig = _create_recovery_pipeline_chart(recovery_data)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # Filterable Recovery Items
    # -----------------------------------------------------------------------
    render_section_header("Manage Individual Recovery Records", "Advance items through lifecycle stages or record outcomes")

    col_flt, col_summary = st.columns([2, 2])
    with col_flt:
        status_filter = st.selectbox(
            "Filter by Pipeline Stage",
            ["All Stages", "Detected", "Disputed", "Under Review", "Recovered", "Rejected"],
            key="recovery_stage_filter",
        )

    filtered_data = recovery_data
    if status_filter != "All Stages":
        filtered_data = [r for r in recovery_data if r.get("status") == status_filter]

    st.markdown(f"**Showing {len(filtered_data)} recovery item(s)**")

    if filtered_data:
        for rec in filtered_data:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2.5, 1.2, 1.5, 1.2])
                prop_name = prop_dict.get(rec.get("property_id"), "Unknown Property")
                amt = float(rec.get("amount", 0.0))
                current_st = rec.get("status", "Detected")

                with c1:
                    st.markdown(f"**🏢 {prop_name}**")
                    if rec.get("notes"):
                        st.caption(f"Note: {rec['notes']}")
                    st.caption(f"Created on: {rec.get('created_at', '')[:10]}")

                with c2:
                    st.markdown(
                        f"""
                        <div style="font-size:0.6875rem; font-weight:700; color:#64748B; text-transform:uppercase;">Recovery Amount</div>
                        <div style="font-size:1.125rem; font-weight:800; color:#16A34A;">{format_currency(amt)}</div>
                        """,
                        unsafe_allow_html=True,
                    )

                with c3:
                    st.markdown(
                        f"""
                        <div style="font-size:0.6875rem; font-weight:700; color:#64748B; text-transform:uppercase; margin-bottom:0.2rem;">Current Stage</div>
                        {render_status_badge(current_st)}
                        """,
                        unsafe_allow_html=True,
                    )

                with c4:
                    st.markdown("<div style='height:0.25rem;'></div>", unsafe_allow_html=True)
                    if current_st == "Detected":
                        if st.button("Dispute →", key=f"rec_dispute_{rec['id']}", use_container_width=True, type="primary"):
                            _update_recovery_status(rec["id"], "Disputed", "Dispute initiated")
                            st.rerun()

                    elif current_st == "Disputed":
                        if st.button("To Review →", key=f"rec_review_{rec['id']}", use_container_width=True):
                            _update_recovery_status(rec["id"], "Under Review", "Submitted for formal review")
                            st.rerun()

                    elif current_st == "Under Review":
                        col_rec, col_rej = st.columns(2)
                        with col_rec:
                            if st.button("Recover", key=f"rec_win_{rec['id']}", type="primary", use_container_width=True):
                                _update_recovery_status(rec["id"], "Recovered", "Funds recovered successfully")
                                st.rerun()
                        with col_rej:
                            if st.button("Reject", key=f"rec_fail_{rec['id']}", use_container_width=True):
                                _update_recovery_status(rec["id"], "Rejected", "Dispute rejected by landlord")
                                st.rerun()

                    elif current_st in ["Recovered", "Rejected"]:
                        st.caption("Lifecycle Finalized")
    else:
        render_empty_state("No Items in This Stage", f"No recovery records currently match stage '{status_filter}'.", "📂")
