"""
Disputes page for LeaseGuard AI.

AI-assisted dispute document generation, human-in-the-loop review,
tone templates, and formal claim export.
"""

from typing import Any, Dict, List
import streamlit as st

from services.auth import get_supabase_client, require_current_user_id
from services.demo import is_demo_mode
from services.extraction import generate_dispute_draft
from ui.custom_theme import COLORS, get_color
from utils.ui import (
    format_currency,
    render_alert,
    render_divider,
    render_empty_state,
    render_page_header,
    render_section_header,
    render_status_badge,
    render_stepper,
)


def _get_disputes() -> List[Dict[str, Any]]:
    """Fetch all disputes."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("disputes").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return response.data or []


def _get_recovery_records() -> List[Dict[str, Any]]:
    """Fetch recovery records."""
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


def _create_dispute(prop_id: str, recovery_id: str, title: str, summary: str) -> Dict[str, Any]:
    """Create a new dispute record."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("disputes").insert({
        "user_id": user_id,
        "property_id": prop_id,
        "recovery_record_id": recovery_id,
        "title": title,
        "summary": summary,
        "status": "Draft",
    }).execute()
    return response.data or []


def _update_dispute_status(dispute_id: str, new_status: str):
    """Update dispute status."""
    client = get_supabase_client()
    client.table("disputes").update({"status": new_status}).eq("id", dispute_id).execute()


def render():
    """Render the dispute generation and management workflow."""
    render_page_header(
        title="Dispute Management & Claims",
        subtitle="Generate formal audit claim letters, review contractual citations, and export dispute documentation.",
        icon="⚖️",
    )

    tab_create, tab_manage = st.tabs(["Draft Dispute Claim", "Dispute Claims Registry"])

    # -----------------------------------------------------------------------
    # TAB 1: DRAFT DISPUTE CLAIM
    # -----------------------------------------------------------------------
    with tab_create:
        # 5-Step Visual Workflow Guide
        render_stepper(["Select Finding", "AI Draft Generation", "Human Review", "Edit & Tone", "Export Claim"], 1)

        st.markdown(
            """
            <div class="alert-box alert-info">
                <strong>Human-in-the-Loop Workflow:</strong>
                LeaseGuard AI synthesizes contractual clauses, audited discrepancy numbers, and legal citations into a formal draft claim. Review, edit, and approve all terms before submission.
            </div>
            """,
            unsafe_allow_html=True,
        )

        properties = _get_properties()
        recovery_records = _get_recovery_records()
        prop_dict = {p["id"]: p["name"] for p in properties}

        if not recovery_records:
            render_empty_state(
                title="No Recovery Items Available",
                description="Run lease audits to discover overcharges and generate claimable recovery items.",
                icon="⚖️",
            )
            return

        render_section_header("01. Select Target Discrepancy", "Choose the flagged overcharge to dispute with the landlord")

        selected_recovery = st.selectbox(
            "Select Recovery Item*",
            options=recovery_records,
            format_func=lambda x: f"{prop_dict.get(x['property_id'], 'Property')} — {format_currency(x.get('amount', 0))} ({x.get('status', 'Detected')})",
            key="dispute_rec_select",
        )

        if selected_recovery:
            prop_name = prop_dict.get(selected_recovery["property_id"], "Unknown Property")
            amount = float(selected_recovery.get("amount", 0))

            render_section_header("02. AI Draft Synthesis", f"Generate claim documentation for {prop_name}")

            col_ai, col_status = st.columns([2, 1])
            with col_ai:
                if st.button("🤖 Generate Draft Claim with AI (RocketRide)", disabled=is_demo_mode(), type="primary"):
                    with st.spinner("Synthesizing lease contract citations and calculation breakdown..."):
                        try:
                            st.session_state["dispute_summary"] = generate_dispute_draft(
                                prop_name, amount, selected_recovery.get("status", "Detected")
                            )
                            render_alert("Draft synthesized! Review and refine the document below.", kind="success", title="Draft Ready")
                        except RuntimeError as exc:
                            render_alert(str(exc), kind="error", title="AI Generation Notice")
            with col_status:
                if is_demo_mode():
                    st.caption("🎭 DEMO MODE: Pre-configured sample dispute template loaded below.")

            # Tone & Template Selector
            with st.expander("Tone & Template Selection", expanded=False):
                template_choice = st.radio(
                    "Claim Tone",
                    ["Standard Professional", "Aggressive Enforcement", "Collaborative Inquiry"],
                    horizontal=True,
                )
                if template_choice == "Aggressive Enforcement":
                    st.session_state["dispute_summary"] = f"""FORMAL NOTICE OF LEASE OVERCHARGE & DEMAND FOR REIMBURSEMENT

To: Landlord / Property Management
Property: {prop_name}
Claim Amount: {format_currency(amount)}
Date: 2026-09-01

Pursuant to Section 8 of the Commercial Lease Agreement and applicable real estate accounting standards, formal notice is hereby served regarding audited discrepancies.

SUMMARY OF AUDIT FINDINGS:
1. CAM charges exceeded contractual year-over-year escalation caps.
2. Unallowable capital expenditures and administrative fees were improperly passed through.
3. Pro-rata tenant share calculations deviated from contractual square footage ratios.

DEMAND:
Immediate reimbursement or rent credit in the sum of {format_currency(amount)} within thirty (30) days.

Respectfully submitted,
Commercial Audit Department
LeaseGuard Compliance Systems
"""

            # Human Review & Edit Form
            render_section_header("03. Human Review & Editing", "Review the letter draft, confirm citation accuracy, and finalize")

            with st.form("finalize_dispute_form", clear_on_submit=False):
                title = st.text_input(
                    "Claim Subject / Title*",
                    value=f"Formal Lease Overcharge Dispute — {prop_name}",
                    placeholder="Enter claim letter title",
                )

                default_body = st.session_state.get(
                    "dispute_summary",
                    f"""FORMAL AUDIT CLAIM NOTICE

Property: {prop_name}
Identified Overcharge: {format_currency(amount)}

Dear Property Management,

Following a detailed deterministic audit of our lease agreement and operating expense reconciliation statements for {prop_name}, our audit team has identified overcharges totaling {format_currency(amount)}.

We request a prompt review of the enclosed line-item findings and credit to our operating account.

Sincerely,
Tenant Lease Compliance Team
""",
                )

                summary = st.text_area(
                    "Dispute Letter Body (Editable)*",
                    value=default_body,
                    height=240,
                    placeholder="Enter formal dispute letter text...",
                )

                submitted = st.form_submit_button("Approve & Register Dispute Claim", type="primary")

                if submitted:
                    if title.strip() and summary.strip():
                        try:
                            _create_dispute(
                                selected_recovery["property_id"],
                                selected_recovery["id"],
                                title,
                                summary,
                            )
                            render_alert("Dispute claim created and registered successfully!", kind="success", title="Claim Registered")
                            st.rerun()
                        except Exception as e:
                            render_alert(f"Error registering dispute: {str(e)}", kind="error")
                    else:
                        render_alert("Title and document summary body are required.", kind="error")

    # -----------------------------------------------------------------------
    # TAB 2: DISPUTE CLAIMS REGISTRY
    # -----------------------------------------------------------------------
    with tab_manage:
        render_section_header("Registered Claims", "Track submitted claims, landlord responses, and export formal letters")

        disputes = _get_disputes()

        if not disputes:
            render_empty_state(
                title="No Dispute Claims Created",
                description="Draft and approve a dispute claim in the 'Draft Dispute Claim' tab to begin tracking formal actions.",
                icon="⚖️",
            )
            return

        status_flt = st.selectbox(
            "Filter by Claim Status",
            ["All Statuses", "Draft", "Submitted", "Under Review", "Accepted", "Rejected", "Recovered"],
            key="disp_status_flt",
        )

        filtered_disputes = disputes
        if status_flt != "All Statuses":
            filtered_disputes = [d for d in disputes if d.get("status") == status_flt]

        st.markdown(f"**{len(filtered_disputes)} registered claim(s)**")

        for dispute in filtered_disputes:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1.2])

                with c1:
                    st.markdown(f"<h3 style='margin:0; font-size:1.125rem;'>{dispute.get('title', 'Dispute Claim')}</h3>", unsafe_allow_html=True)
                    st.caption(f"Created: {dispute.get('created_at', '')[:10]}")

                    with st.expander("Read Formal Claim Text", expanded=False):
                        st.text(dispute.get("summary", ""))

                with c2:
                    current_st = dispute.get("status", "Draft")
                    st.markdown(
                        f"""
                        <div style="font-size:0.6875rem; font-weight:700; color:#64748B; text-transform:uppercase; margin-bottom:0.2rem;">Claim Status</div>
                        {render_status_badge(current_st)}
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

                    if current_st == "Draft":
                        if st.button("Mark Submitted", key=f"submit_disp_{dispute['id']}", type="primary", use_container_width=True):
                            _update_dispute_status(dispute["id"], "Submitted")
                            st.rerun()

                    export_text = f"""=======================================================
LEASEGUARD AI — FORMAL DISPUTE CLAIM DOCUMENTATION
=======================================================
Title:  {dispute.get('title', 'Lease Dispute')}
Date:   {dispute.get('created_at', '2026-09-01')}
Status: {dispute.get('status', 'Draft')}

-------------------------------------------------------
CLAIM CONTENT
-------------------------------------------------------
{dispute.get('summary', '')}

=======================================================
Generated via LeaseGuard AI Enterprise Audit Platform
=======================================================
"""
                    st.download_button(
                        label="Download Export (.txt)",
                        data=export_text,
                        file_name=f"lease_dispute_{dispute['id'][:8]}.txt",
                        mime="text/plain",
                        key=f"dl_disp_{dispute['id']}",
                        use_container_width=True,
                    )
