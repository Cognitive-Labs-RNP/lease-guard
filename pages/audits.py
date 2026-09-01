"""
Audits page for LeaseGuard AI.

Run deterministic lease vs invoice audits with structured reconciliation,
risk score calculations, and contract evidence inspection.
"""

from typing import Any, Dict, List, Optional, Tuple
import streamlit as st

from services.audit_engine import audit_lease_invoice
from services.auth import get_supabase_client, require_current_user_id
from services.demo import is_demo_mode
from services.extraction import get_sample_invoice_data, get_sample_lease_data
from services.recovery_engine import build_recovery_summary
from services.risk_engine import calculate_risk_score
from services.supabase_persistence import save_audit_result
from services.validation import extract_summary, validate_audit_ready, validate_invoice_data, validate_lease_data
from ui.custom_theme import COLORS, get_color
from utils.ui import (
    format_currency,
    render_alert,
    render_divider,
    render_empty_state,
    render_finding_card,
    render_kpi_card,
    render_page_header,
    render_section_header,
    render_status_badge,
    render_stepper,
)


def _get_properties() -> List[Dict[str, Any]]:
    """Fetch user's properties."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("properties").select("id, name").eq("user_id", user_id).order("name").execute()
    return response.data or []


def _get_property_documents(prop_id: str, doc_type: str) -> List[Dict[str, Any]]:
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


def _get_property_audits(prop_id: str) -> List[Dict[str, Any]]:
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
    lease_docs: List[Dict[str, Any]], invoice_docs: List[Dict[str, Any]]
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Attempt to load extracted structured data from uploaded documents."""
    lease_data = None
    invoice_data = None

    if lease_docs:
        latest_lease = lease_docs[0]
        doc_meta = latest_lease.get("metadata", {})
        if doc_meta.get("extracted_data"):
            lease_data = doc_meta.get("extracted_data")

    if invoice_docs:
        latest_invoice = invoice_docs[0]
        doc_meta = latest_invoice.get("metadata", {})
        if doc_meta.get("extracted_data"):
            invoice_data = doc_meta.get("extracted_data")

    return lease_data, invoice_data


def render():
    """Render the deterministic audit execution engine and history."""
    render_page_header(
        title="Lease Audit Sessions",
        subtitle="Reconcile contractual lease provisions against landlord invoice charges with mathematical certainty.",
        icon="🔎",
    )

    tab_run, tab_history = st.tabs(["Execute Audit Session", "Audit Log & History"])

    # -----------------------------------------------------------------------
    # TAB 1: RUN AUDIT SESSION
    # -----------------------------------------------------------------------
    with tab_run:
        properties = _get_properties()

        if not properties:
            render_empty_state(
                title="No Properties Available",
                description="Register a commercial property first to begin conducting lease reconciliation audits.",
                icon="🏢",
            )
            return

        # Visual Stepper
        render_stepper(["Select Property", "Contract Terms", "Invoice Charges", "Deterministic Reconciliation"], 0)

        prop_dict = {p["id"]: p["name"] for p in properties}
        selected_prop_id = st.selectbox(
            "Target Commercial Property*",
            options=[p["id"] for p in properties],
            format_func=lambda x: prop_dict.get(x, "Unknown"),
            key="audit_target_prop",
        )

        if selected_prop_id:
            prop_name = prop_dict[selected_prop_id]
            lease_docs = _get_property_documents(selected_prop_id, "Lease")
            invoice_docs = _get_property_documents(selected_prop_id, "Invoice")
            extracted_lease, extracted_invoice = _load_extracted_data_from_documents(lease_docs, invoice_docs)

            # ---------------------------------------------------------------
            # 1. Lease Terms Section
            # ---------------------------------------------------------------
            render_section_header("01. Contractual Lease Terms", f"Provisions and expense caps governing {prop_name}")

            if extracted_lease and lease_docs:
                st.markdown(
                    f"<div style='color:#15803D; font-size:0.875rem; font-weight:600; margin-bottom:0.5rem;'>✓ Pre-filled from extracted document: {lease_docs[0].get('file_name')}</div>",
                    unsafe_allow_html=True,
                )

            with st.expander("Review & Confirm Lease Terms", expanded=True):
                col_l1, col_l2 = st.columns(2)
                with col_l1:
                    base_rent = st.number_input(
                        "Annual Base Rent ($)*",
                        min_value=0.0,
                        value=float(extracted_lease.get("base_rent", 120000) if extracted_lease else 120000),
                        step=1000.0,
                        help="Contractual annual base rent",
                    )
                    cam_cap_pct = st.number_input(
                        "CAM Expense Cap (%)*",
                        min_value=0.0,
                        max_value=100.0,
                        value=float((extracted_lease.get("cam_cap_pct", 0.05) * 100) if extracted_lease else 5.0),
                        step=0.5,
                        help="Maximum allowable annual CAM increase as percentage",
                    ) / 100.0

                with col_l2:
                    tenant_share = st.number_input(
                        "Tenant Pro-Rata Share (%)*",
                        min_value=0.0,
                        max_value=100.0,
                        value=float((extracted_lease.get("tenant_share_pct", 0.25) * 100) if extracted_lease else 25.0),
                        step=0.5,
                        help="Tenant's pro-rata percentage share of building expenses",
                    ) / 100.0
                    annual_increase = st.number_input(
                        "Annual Rent Escalation (%)",
                        min_value=0.0,
                        max_value=25.0,
                        value=float((extracted_lease.get("annual_increase_pct", 0.03) * 100) if extracted_lease else 3.0),
                        step=0.5,
                        help="Contractual annual base rent escalation rate",
                    ) / 100.0

                lease_data = {
                    "base_rent": base_rent,
                    "cam_cap_pct": cam_cap_pct,
                    "tenant_share_pct": tenant_share,
                    "annual_increase_pct": annual_increase,
                    "current_rent": base_rent,
                    "excluded_expenses": ["management_fee"],
                }

            # ---------------------------------------------------------------
            # 2. Invoice Charges Section
            # ---------------------------------------------------------------
            render_section_header("02. Landlord Invoice & Operating Charges", f"Statement amounts billed for reconciliation")

            if extracted_invoice and invoice_docs:
                st.markdown(
                    f"<div style='color:#15803D; font-size:0.875rem; font-weight:600; margin-bottom:0.5rem;'>✓ Pre-filled from statement: {invoice_docs[0].get('file_name')}</div>",
                    unsafe_allow_html=True,
                )

            with st.expander("Review & Confirm Invoice Line Items", expanded=True):
                col_i1, col_i2 = st.columns(2)
                with col_i1:
                    rent_amount = st.number_input(
                        "Billed Base Rent ($)*",
                        min_value=0.0,
                        value=float(extracted_invoice.get("rent_amount", 10000) if extracted_invoice else 10000),
                        step=500.0,
                    )
                    cam_expense = st.number_input(
                        "Billed Common Area Maintenance (CAM) ($)*",
                        min_value=0.0,
                        value=float(extracted_invoice.get("cam_expense", 1500) if extracted_invoice else 1500),
                        step=100.0,
                    )

                with col_i2:
                    admin_fee = st.number_input(
                        "Billed Administrative / Management Fee ($)",
                        min_value=0.0,
                        value=float(extracted_invoice.get("admin_fee_amount", 500) if extracted_invoice else 500),
                        step=50.0,
                    )
                    tax_amount = st.number_input(
                        "Billed Real Estate Taxes ($)",
                        min_value=0.0,
                        value=float(extracted_invoice.get("tax_amount", 0) if extracted_invoice else 0),
                        step=50.0,
                    )

                invoice_data = {
                    "cam_expense": cam_expense,
                    "rent_amount": rent_amount,
                    "admin_fee_amount": admin_fee,
                    "tax_amount": tax_amount,
                    "tenant_share_pct": lease_data.get("tenant_share_pct", 0.25),
                    "total_amount": rent_amount + cam_expense + admin_fee + tax_amount,
                }

            # ---------------------------------------------------------------
            # 3. Validation & Execution
            # ---------------------------------------------------------------
            render_divider("1.5rem")
            is_ready, validation_errors = validate_audit_ready(lease_data, invoice_data)

            if is_ready:
                col_btn, col_info = st.columns([1.5, 3])
                with col_btn:
                    run_clicked = st.button("▶ Run Deterministic Audit", type="primary", use_container_width=True)
                with col_info:
                    st.markdown(
                        "<div style='font-size:0.8125rem; color:#64748B; padding-top:0.4rem;'>Executes CAM cap checks, exclusion enforcement, escalation rules, and pro-rata share reconciliation.</div>",
                        unsafe_allow_html=True,
                    )

                if run_clicked:
                    with st.status("Executing Deterministic Lease Audit...", expanded=True) as status_box:
                        st.write("1. Reading contractual lease provisions & exclusion clauses...")
                        findings = audit_lease_invoice(lease_data, invoice_data)

                        st.write("2. Reconciling billed line items against contractual caps...")
                        category_scores = {
                            "cam_risk": 50 if any(f.get("category") == "CAM cap" for f in findings) else 10,
                            "rent_escalation_risk": 40 if any(f.get("category") == "Rent escalation" for f in findings) else 5,
                            "administrative_fee_risk": 30 if any(f.get("category") == "Administrative fee" for f in findings) else 5,
                            "tax_risk": 20,
                            "audit_rights_risk": 25,
                        }

                        st.write("3. Calculating risk score exposure & recovery potentials...")
                        risk = calculate_risk_score(category_scores)
                        recovery = build_recovery_summary(findings)

                        st.write("4. Persisting audit findings & recovery pipeline records...")
                        save_audit_result(
                            property_id=selected_prop_id,
                            audit_type="Deterministic Lease Audit",
                            total_invoice_amount=invoice_data.get("total_amount", 0),
                            findings=findings,
                            overall_score=risk["overall_score"],
                            risk_level=risk["risk_level"],
                            recovery_summary=recovery,
                            notes="Automated deterministic audit with contractual evidence",
                        )
                        status_box.update(label="✓ Audit Complete — Discrepancies Calculated", state="complete")

                    # -------------------------------------------------------
                    # Audit Results Display
                    # -------------------------------------------------------
                    render_section_header("Audit Results & Summary", f"Reconciliation summary for {prop_name}")

                    r_col1, r_col2, r_col3 = st.columns(3)
                    with r_col1:
                        render_kpi_card(
                            label="Total Discrepancies",
                            value=str(len(findings)),
                            context="Flagged lease issues",
                            icon="🔍",
                            accent_color=get_color("brand_blue"),
                        )
                    with r_col2:
                        risk_score = risk["overall_score"]
                        risk_accent = (
                            get_color("risk_critical") if risk_score >= 70
                            else get_color("risk_high") if risk_score >= 50
                            else get_color("risk_moderate") if risk_score >= 30
                            else get_color("risk_low")
                        )
                        render_kpi_card(
                            label="Calculated Risk Score",
                            value=f"{risk_score:.0f} / 100",
                            context=f"● {risk['risk_level'].upper()}",
                            icon="📊",
                            accent_color=risk_accent,
                        )
                    with r_col3:
                        render_kpi_card(
                            label="Potential Recovery",
                            value=format_currency(recovery["potential_recovery"]),
                            context="Contract overcharges",
                            icon="💰",
                            accent_color=get_color("success"),
                        )

                    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
                    render_section_header("Discrepancy Breakdown", "Individual findings with financial comparison and contract evidence")

                    if findings:
                        for finding in findings:
                            billed_amt = float(finding.get("billed_amount") or finding.get("amount") or 0.0)
                            allowed_amt = float(finding.get("allowed_amount") or 0.0)
                            potential_rec = float(finding.get("potential_recovery") or finding.get("amount") or 0.0)
                            evidence_text = finding.get("lease_evidence", {}).get("clause", "") or finding.get("explanation", "")

                            render_finding_card(
                                category=finding.get("category", "Finding"),
                                title=finding.get("title", finding.get("category", "Discrepancy")),
                                description=finding.get("explanation", ""),
                                severity=finding.get("severity", "Medium"),
                                billed=billed_amt,
                                allowed=allowed_amt,
                                recovery=potential_rec,
                                evidence=evidence_text,
                                property_name=prop_name,
                            )
                    else:
                        render_empty_state("Zero Discrepancies Detected", "All invoice charges strictly adhered to lease caps and allowances.", "✅")

            else:
                render_alert("Please resolve the following input issues before running the audit:", kind="error", title="Validation Blocked")
                for err in validation_errors:
                    st.write(f"• {err}")

    # -----------------------------------------------------------------------
    # TAB 2: AUDIT HISTORY
    # -----------------------------------------------------------------------
    with tab_history:
        render_section_header("Audit Session Archive", "Historical audit records and full execution traces")

        prop_dict_hist = {p["id"]: p["name"] for p in properties}
        selected_hist_prop_id = st.selectbox(
            "Filter by Property",
            options=[p["id"] for p in properties],
            format_func=lambda x: prop_dict_hist.get(x, "Unknown"),
            key="hist_prop_select",
        )

        if selected_hist_prop_id:
            audits = _get_property_audits(selected_hist_prop_id)

            if audits:
                st.markdown(f"**{len(audits)} recorded audit session(s)**")

                for audit in audits:
                    with st.container(border=True):
                        c1, c2, c3, c4 = st.columns([2, 1, 1, 0.8])
                        with c1:
                            st.markdown(f"**{audit.get('audit_type', 'Audit Session')}**")
                            st.caption(f"Session date: {audit.get('created_at', '')[:10]}")
                        with c2:
                            st.markdown(
                                f"<span style='font-size:0.75rem; color:#667085; text-transform:uppercase; font-weight:700;'>Status</span><br>{render_status_badge(audit.get('status', 'resolved'))}",
                                unsafe_allow_html=True,
                            )
                        with c3:
                            st.markdown(
                                f"<span style='font-size:0.75rem; color:#667085; text-transform:uppercase; font-weight:700;'>Invoice Total</span><br><strong>{format_currency(audit.get('total_invoice_amount', 0))}</strong>",
                                unsafe_allow_html=True,
                            )
                        with c4:
                            st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
                            with st.expander("Inspect"):
                                st.json(audit)
            else:
                render_empty_state("No Previous Audits", f"No historical audits found for {prop_dict_hist.get(selected_hist_prop_id)}.", "📁")
