"""
Disputes page for LeaseGuard.

Manage disputes and export dispute documentation.
"""

from typing import Any, Dict

import streamlit as st

from services.auth import get_supabase_client, require_current_user_id
from services.demo import is_demo_mode
from services.extraction import generate_dispute_draft
from ui.custom_theme import COLORS, get_color


def _get_disputes() -> list[Dict[str, Any]]:
    """Fetch all disputes."""
    user_id = require_current_user_id()
    client = get_supabase_client()

    response = client.table("disputes").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return response.data or []


def _get_recovery_records() -> list[Dict[str, Any]]:
    """Fetch recovery records."""
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


def _create_dispute(prop_id: str, recovery_id: str, title: str, summary: str) -> Dict[str, Any]:
    """Create a new dispute."""
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
    """Render the disputes page."""
    st.markdown("## ⚖️ Disputes")

    tab1, tab2 = st.tabs(["Create Dispute", "View Disputes"])

    with tab1:
        st.markdown("### Generate Dispute Documentation")

        properties = _get_properties()
        recovery_records = _get_recovery_records()
        prop_dict = {p["id"]: p["name"] for p in properties}

        if not recovery_records:
            st.info("No recovery records yet. Run audits to generate recovery items.")
            return

        # Recovery selection
        selected_recovery = st.selectbox(
            "Select Recovery Item",
            options=recovery_records,
            format_func=lambda x: f"{prop_dict.get(x['property_id'], 'Unknown')} - ${float(x.get('amount', 0)):,.2f}",
            key="dispute_recovery_select"
        )

        if selected_recovery:
            st.markdown("---")
            st.markdown("### Dispute Details")

            prop_name = prop_dict.get(selected_recovery["property_id"], "Unknown")
            amount = float(selected_recovery.get("amount", 0))

            if st.button("Generate draft with RocketRide", disabled=is_demo_mode()):
                try:
                    st.session_state["dispute_summary"] = generate_dispute_draft(
                        prop_name, amount, selected_recovery.get("status", "Detected")
                    )
                    st.success("Draft generated. Review and edit it before creating the dispute.")
                except RuntimeError as exc:
                    st.error(str(exc))
                    st.info("You can continue by writing the dispute summary manually.")
            if is_demo_mode():
                st.caption("DEMO / SAMPLE DATA: RocketRide generation is disabled; use the editable sample draft below.")

            with st.form("create_dispute_form"):
                st.write(f"**Property**: {prop_name}")
                st.write(f"**Recovery Amount**: ${amount:,.2f}")
                st.write(f"**Recovery Status**: {selected_recovery.get('status', 'N/A')}")

                st.markdown("---")

                title = st.text_input(
                    "Dispute Title",
                    value=f"Recovery Claim for {prop_name}",
                    placeholder="Enter dispute title"
                )

                summary = st.text_area(
                    "Dispute Summary",
                    value=st.session_state.get("dispute_summary", f"Dispute for recovery of ${amount:,.2f} from {prop_name}. This dispute is based on findings from deterministic lease audit."),
                    placeholder="Describe the dispute",
                    height=200
                )

                # Dispute template options
                with st.expander("Dispute Template", expanded=False):
                    template = st.radio(
                        "Select Template",
                        ["Standard", "Aggressive", "Conservative"],
                        key="dispute_template"
                    )

                    if template == "Aggressive":
                        summary = f"""
DEMAND FOR RECOVERY OF OVERCHARGES

Property: {prop_name}
Claim Amount: ${amount:,.2f}

Pursuant to the lease agreement and applicable law, we hereby demand payment of overcharges identified in our audit.

FINDINGS:
- CAM charges exceeded contractual caps
- Administrative fees exceeded allowable amounts
- Excluded expenses were improperly billed

This dispute is filed under protest and without waiver of rights.

Respectfully submitted,
LeaseGuard AI
"""

                submitted = st.form_submit_button("Create Dispute", type="primary")

                if submitted:
                    if title.strip() and summary.strip():
                        try:
                            _create_dispute(
                                selected_recovery["property_id"],
                                selected_recovery["id"],
                                title,
                                summary
                            )
                            st.success("Dispute created successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creating dispute: {str(e)}")
                    else:
                        st.error("Title and summary are required")

    with tab2:
        st.markdown("### Dispute Management")

        disputes = _get_disputes()

        if not disputes:
            st.info("No disputes yet")
            return

        # Status filter
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "Draft", "Submitted", "Under Review", "Accepted", "Rejected", "Recovered"],
            key="dispute_status_filter"
        )

        # Filter
        filtered_disputes = disputes
        if status_filter != "All":
            filtered_disputes = [d for d in disputes if d.get("status") == status_filter]

        st.markdown(f"**{len(filtered_disputes)} disputes**")

        for dispute in filtered_disputes:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"### {dispute.get('title', 'N/A')}")
                    st.write(f"**Status**: {dispute.get('status', 'N/A')}")
                    st.write(f"**Date**: {dispute.get('created_at', 'N/A')[:10]}")

                    with st.expander("View Summary"):
                        st.write(dispute.get("summary", "N/A"))

                with col2:
                    current_status = dispute.get("status", "Draft")

                    if current_status == "Draft":
                        if st.button("Submit", key=f"submit_{dispute['id']}", type="primary"):
                            _update_dispute_status(dispute["id"], "Submitted")
                            st.success("Dispute submitted")
                            st.rerun()

                        if st.button("Edit", key=f"edit_{dispute['id']}"):
                            st.write("Edit functionality not yet implemented")

                    elif current_status == "Submitted":
                        st.write("✅ Submitted")

                    elif current_status in ["Accepted", "Recovered"]:
                        st.write(f"✅ {current_status}")

                    elif current_status == "Rejected":
                        st.write("❌ Rejected")

                    if st.button("Export", key=f"export_{dispute['id']}"):
                        export_text = f"""
=====================================
DISPUTE DOCUMENTATION
=====================================

Title: {dispute.get('title', 'N/A')}
Date: {dispute.get('created_at', 'N/A')}
Status: {dispute.get('status', 'N/A')}

{dispute.get('summary', 'N/A')}

=====================================
Generated by LeaseGuard AI
"""
                        st.download_button(
                            label="Download Dispute",
                            data=export_text,
                            file_name=f"dispute_{dispute['id'][:8]}.txt",
                            mime="text/plain"
                        )
