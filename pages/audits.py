"""
Audits page for LeaseGuard.

Run lease audits and view results.
Integrates extraction, validation, and deterministic audit engine.
"""

from typing import Any, Dict, Optional, Tuple

import streamlit as st

from services.audit_engine import audit_lease_invoice
from services.recovery_engine import build_recovery_summary
from services.risk_engine import calculate_risk_score
from services.supabase_persistence import save_audit_result
from services.auth import get_supabase_client, require_current_user_id
from services.validation import validate_lease_data, validate_invoice_data, validate_audit_ready, extract_summary
from services.extraction import get_sample_lease_data, get_sample_invoice_data
from services.demo import is_demo_mode
from ui.custom_theme import COLORS, get_color


def _get_properties() -> list[Dict[str, Any]]:
    """Fetch user's properties."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("properties").select("id, name").eq("user_id", user_id).order("name").execute()
    return response.data or []


def _get_property_documents(prop_id: str, doc_type: str) -> list[Dict[str, Any]]:
    """Fetch documents of a specific type for a property."""
    client = get_supabase_client()
    response = (
        client.table("documents")
        .select("*")
        .eq("property_id", prop_id)
        .eq("document_type", doc_type)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def _get_property_audits(prop_id: str) -> list[Dict[str, Any]]:
    """Fetch audits for a property."""
    client = get_supabase_client()
    response = (
        client.table("audits")
        .select("*")
        .eq("property_id", prop_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def _load_extracted_data_from_documents(
    lease_docs: list[Dict[str, Any]], invoice_docs: list[Dict[str, Any]]
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """
    Attempt to load extracted data from uploaded documents.

    Returns:
        Tuple of (lease_data, invoice_data), each can be None if not found
    """
    lease_data = None
    invoice_data = None

    # Try to get lease data from latest lease document
    if lease_docs:
        latest_lease = lease_docs[0]
        doc_meta = latest_lease.get("metadata", {})
        if doc_meta.get("extracted_data"):
            lease_data = doc_meta.get("extracted_data")

    # Try to get invoice data from latest invoice document
    if invoice_docs:
        latest_invoice = invoice_docs[0]
        doc_meta = latest_invoice.get("metadata", {})
        if doc_meta.get("extracted_data"):
            invoice_data = doc_meta.get("extracted_data")

    return lease_data, invoice_data


def render():
    """Render the audits page."""
    st.markdown("## 🔎 Audits")

    if is_demo_mode():
        st.info("🎭 **DEMO MODE** — Using sample data for demonstration")

    tab1, tab2 = st.tabs(["Run Audit", "Audit History"])

    with tab1:
        st.markdown("### Create New Audit")

        properties = _get_properties()

        if not properties:
            st.info("No properties yet. Create a property first.")
            return

        prop_dict = {p["id"]: p["name"] for p in properties}

        # Property selection
        selected_prop_id = st.selectbox(
            "Select Property",
            options=[p["id"] for p in properties],
            format_func=lambda x: prop_dict.get(x, "Unknown"),
            key="audit_prop_select"
        )

        if selected_prop_id:
            # Load documents
            lease_docs = _get_property_documents(selected_prop_id, "Lease")
            invoice_docs = _get_property_documents(selected_prop_id, "Invoice")

            # Try to load extracted data from documents
            extracted_lease, extracted_invoice = _load_extracted_data_from_documents(lease_docs, invoice_docs)

            # ================================================================
            # Lease Data Section
            # ================================================================
            st.markdown("### Lease Data")

            if lease_docs:
                st.write(f"✓ {len(lease_docs)} lease document(s) available")
                if extracted_lease:
                    st.success(f"✓ Data extracted from: **{lease_docs[0].get('file_name')}**")
            else:
                st.info("No lease documents uploaded yet. Upload a lease document or enter data manually.")

            with st.expander("Edit Lease Terms", expanded=(not extracted_lease)):
                st.markdown("Fill in lease terms below:")

                base_rent = st.number_input(
                    "Base Rent (annual, $)",
                    min_value=0.0,
                    value=float(extracted_lease.get("base_rent", 120000) if extracted_lease else 120000),
                    help="Annual base rent amount"
                )

                cam_cap_pct = st.number_input(
                    "CAM Cap (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float((extracted_lease.get("cam_cap_pct", 0.05) * 100) if extracted_lease else 5.0),
                    help="Maximum CAM increase as percentage of base rent"
                ) / 100

                tenant_share = st.number_input(
                    "Tenant Share (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float((extracted_lease.get("tenant_share_pct", 0.25) * 100) if extracted_lease else 25.0),
                    help="Tenant's share of operating expenses"
                ) / 100

                annual_increase = st.number_input(
                    "Annual Rent Increase (%)",
                    min_value=0.0,
                    max_value=20.0,
                    value=float((extracted_lease.get("annual_increase_pct", 0.03) * 100) if extracted_lease else 3.0),
                    help="Annual rent escalation percentage"
                ) / 100

                lease_data = {
                    "base_rent": base_rent,
                    "cam_cap_pct": cam_cap_pct,
                    "tenant_share_pct": tenant_share,
                    "annual_increase_pct": annual_increase,
                    "current_rent": base_rent,
                    "excluded_expenses": ["management_fee"],
                }

            # Validate lease data
            lease_valid, lease_errors = validate_lease_data(lease_data)
            if not lease_valid:
                with st.expander("⚠ Lease Validation Issues"):
                    for error in lease_errors:
                        st.write(f"• {error}")

            # ================================================================
            # Invoice Data Section
            # ================================================================
            st.markdown("### Invoice Data")

            if invoice_docs:
                st.write(f"✓ {len(invoice_docs)} invoice document(s) available")
                if extracted_invoice:
                    st.success(f"✓ Data extracted from: **{invoice_docs[0].get('file_name')}**")
            else:
                st.info("No invoice documents uploaded yet. Upload an invoice document or enter data manually.")

            with st.expander("Edit Invoice Items", expanded=(not extracted_invoice)):
                st.markdown("Fill in invoice details below:")

                cam_expense = st.number_input(
                    "CAM Charge ($)",
                    min_value=0.0,
                    value=float(extracted_invoice.get("cam_expense", 1500) if extracted_invoice else 1500),
                    help="Common Area Maintenance charge on invoice"
                )

                rent_amount = st.number_input(
                    "Rent Amount ($)",
                    min_value=0.0,
                    value=float(extracted_invoice.get("rent_amount", 10000) if extracted_invoice else 10000),
                    help="Rent portion of the invoice"
                )

                admin_fee = st.number_input(
                    "Administrative Fee ($)",
                    min_value=0.0,
                    value=float(extracted_invoice.get("admin_fee_amount", 500) if extracted_invoice else 500),
                    help="Administrative or management fee on invoice"
                )

                tax_amount = st.number_input(
                    "Tax Amount ($)",
                    min_value=0.0,
                    value=float(extracted_invoice.get("tax_amount", 0) if extracted_invoice else 0),
                    help="Tax or other charges on invoice"
                )

                invoice_data = {
                    "cam_expense": cam_expense,
                    "rent_amount": rent_amount,
                    "admin_fee_amount": admin_fee,
                    "tax_amount": tax_amount,
                    "tenant_share_pct": lease_data.get("tenant_share_pct", 0.25),
                    "total_amount": rent_amount + cam_expense + admin_fee + tax_amount,
                }

            # Validate invoice data
            invoice_valid, invoice_errors = validate_invoice_data(invoice_data)
            if not invoice_valid:
                with st.expander("⚠ Invoice Validation Issues"):
                    for error in invoice_errors:
                        st.write(f"• {error}")

            # ================================================================
            # Overall Validation & Audit Execution
            # ================================================================
            st.markdown("### Validation & Audit")

            is_audit_ready, all_errors = validate_audit_ready(lease_data, invoice_data)

            if is_audit_ready:
                st.success("✅ All data is valid and ready for audit")

                # Run audit button
                if st.button("▶ Run Deterministic Audit", type="primary"):
                    with st.spinner("Running deterministic lease audit..."):
                        try:
                            # Run audit engine
                            findings = audit_lease_invoice(lease_data, invoice_data)

                            # Calculate risk
                            category_scores = {
                                "cam_risk": 50 if any(f["category"] == "CAM cap" for f in findings) else 10,
                                "rent_escalation_risk": 40 if any(f["category"] == "Rent escalation" for f in findings) else 5,
                                "administrative_fee_risk": 30 if any(f["category"] == "Administrative fee" for f in findings) else 5,
                                "tax_risk": 20,
                                "audit_rights_risk": 25,
                            }
                            risk = calculate_risk_score(category_scores)

                            # Build recovery
                            recovery = build_recovery_summary(findings)

                            # Save to Supabase
                            result = save_audit_result(
                                property_id=selected_prop_id,
                                audit_type="Deterministic Lease Audit",
                                total_invoice_amount=invoice_data.get("total_amount", 0),
                                findings=findings,
                                overall_score=risk["overall_score"],
                                risk_level=risk["risk_level"],
                                recovery_summary=recovery,
                                notes="Automated deterministic audit via extraction and validation"
                            )

                            st.success(f"✅ Audit completed! Found {len(findings)} findings.")

                            # Display results
                            st.markdown("---")
                            st.markdown("### Audit Results")

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Findings", len(findings))
                            with col2:
                                st.metric("Risk Score", f"{risk['overall_score']}/100", f"{risk['risk_level']}")
                            with col3:
                                st.metric("Recovery Potential", f"${recovery['potential_recovery']:,.2f}")

                            # Findings detail by severity
                            st.markdown("### Findings Detail")

                            for finding in findings:
                                with st.container(border=True):
                                    col_cat, col_sev, col_amt = st.columns([2, 1, 1])

                                    with col_cat:
                                        st.write(f"**{finding['category']}**")
                                    with col_sev:
                                        st.write(f"🔴 {finding['severity']}" if finding["severity"] == "Critical"
                                                 else f"🟠 {finding['severity']}" if finding["severity"] == "High"
                                                 else f"🟡 {finding['severity']}" if finding["severity"] == "Medium"
                                                 else f"🟢 {finding['severity']}")
                                    with col_amt:
                                        st.write(f"${finding['potential_recovery']:,.2f}")

                                    st.write(finding['explanation'])

                                    # Show evidence in expander
                                    with st.expander("View Evidence"):
                                        if finding.get("lease_evidence"):
                                            st.write("**Lease Evidence:**")
                                            st.json(finding["lease_evidence"])
                                        if finding.get("invoice_evidence"):
                                            st.write("**Invoice Evidence:**")
                                            st.json(finding["invoice_evidence"])

                        except Exception as e:
                            st.error(f"❌ Audit failed: {str(e)}")
                            st.info("Check your database connection and ensure Supabase is properly configured.")

            else:
                st.error("❌ Cannot run audit - data validation issues found:")
                for error in all_errors:
                    st.write(f"• {error}")

    with tab2:
        st.markdown("### Audit History")

        properties = _get_properties()
        prop_dict = {p["id"]: p["name"] for p in properties}

        if not properties:
            st.info("No properties yet")
            return

        # Select property
        selected_prop_id = st.selectbox(
            "Select Property",
            options=[p["id"] for p in properties],
            format_func=lambda x: prop_dict.get(x, "Unknown"),
            key="history_prop_select"
        )

        if selected_prop_id:
            audits = _get_property_audits(selected_prop_id)

            if audits:
                st.markdown(f"**{len(audits)} audit(s)**")

                for audit in audits:
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([2, 1, 1])

                        with col1:
                            st.write(f"**{audit.get('audit_type', 'Audit')}**")
                            st.caption(f"{audit.get('created_at', 'N/A')[:10]}")

                        with col2:
                            st.write(f"Status: **{audit.get('status', 'unknown')}**")

                        with col3:
                            st.write(f"**${float(audit.get('total_invoice_amount', 0)):,.0f}**")

                        # Show notes if available
                        if audit.get("notes"):
                            st.caption(f"Notes: {audit['notes']}")

                        if st.button("View Full Details", key=f"audit_{audit['id']}"):
                            st.json(audit)
            else:
                st.info("No audits for this property yet")
