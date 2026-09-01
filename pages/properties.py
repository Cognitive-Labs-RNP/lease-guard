"""
Properties page for LeaseGuard AI.

Manage real estate portfolio assets, inspect property risk profiles,
and review audit history.
"""

from typing import Any, Dict, Optional
import streamlit as st

from services.auth import get_supabase_client, require_current_user_id
from ui.custom_theme import COLORS, get_color
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


def _get_properties() -> list:
    """Fetch user's active properties."""
    user_id = require_current_user_id()
    client = get_supabase_client()

    response = client.table("properties").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return response.data or []


def _get_property_risk_score(prop_id: str) -> Optional[Dict[str, Any]]:
    """Fetch most recent risk score for property."""
    client = get_supabase_client()
    response = (
        client.table("risk_scores")
        .select("overall_score, risk_level, score_breakdown")
        .eq("property_id", prop_id)
        .order("calculated_at", desc=True)
        .limit(1)
        .execute()
    )
    return (response.data or [None])[0]


def _get_property_audits(prop_id: str) -> list:
    """Fetch audits for property."""
    client = get_supabase_client()
    response = (
        client.table("audits")
        .select("*")
        .eq("property_id", prop_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def _get_property_findings(prop_id: str) -> list:
    """Fetch findings for property."""
    client = get_supabase_client()
    response = (
        client.table("findings")
        .select("*")
        .eq("property_id", prop_id)
        .order("severity", desc=True)
        .execute()
    )
    return response.data or []


def _get_property_recovery(prop_id: str) -> list:
    """Fetch recovery records for property."""
    client = get_supabase_client()
    response = (
        client.table("recovery_records")
        .select("*")
        .eq("property_id", prop_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def _create_property(name: str, address: str, city: str, state: str, postal_code: str, country: str, prop_type: str):
    """Create a new property in Supabase."""
    user_id = require_current_user_id()
    client = get_supabase_client()

    response = client.table("properties").insert({
        "user_id": user_id,
        "name": name,
        "address": address,
        "city": city,
        "state": state,
        "postal_code": postal_code,
        "country": country,
        "property_type": prop_type,
        "status": "active",
    }).execute()

    return response.data or []


def render():
    """Render the properties page."""
    render_page_header(
        title="Portfolio Properties",
        subtitle="Manage commercial real estate properties, inspect lease compliance, and monitor asset risks.",
        icon="🏢",
    )

    tab_all, tab_add = st.tabs(["Portfolio Directory", "Add New Property"])

    # -----------------------------------------------------------------------
    # TAB 1: ALL PROPERTIES
    # -----------------------------------------------------------------------
    with tab_all:
        properties = _get_properties()

        if not properties:
            render_empty_state(
                title="No Properties In Portfolio",
                description="Add your first commercial property in the 'Add New Property' tab to begin auditing lease agreements and monitoring operating expenses.",
                icon="🏢",
            )
        else:
            # Summary KPI row
            active_count = sum(1 for p in properties if p.get("status") == "active")
            inactive_count = len(properties) - active_count

            col1, col2, col3 = st.columns(3)
            with col1:
                render_kpi_card("Total Properties", str(len(properties)), "Registered assets", "🏢", get_color("brand_blue"))
            with col2:
                render_kpi_card("Active Monitoring", str(active_count), "Compliant tracking", "🟢", get_color("success"))
            with col3:
                render_kpi_card("Archived / Inactive", str(inactive_count), "Non-active leases", "⚪", get_color("border_strong"))

            st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)
            render_section_header("Property Inspector", "Select a property to view risk metrics, audit history, and financial recoveries")

            # Property Selector
            prop_names = [p["name"] for p in properties]
            selected_name = st.selectbox("Select Property to Inspect", prop_names, key="prop_inspector_select")

            selected_prop = next((p for p in properties if p["name"] == selected_name), None)

            if selected_prop:
                prop_id = selected_prop["id"]
                risk = _get_property_risk_score(prop_id)

                with st.container(border=True):
                    # Header row inside card
                    c_title, c_status = st.columns([3, 1])
                    with c_title:
                        st.markdown(f"<h2 style='margin:0; font-size:1.375rem;'>{selected_prop['name']}</h2>", unsafe_allow_html=True)
                        st.markdown(
                            f"<p style='color:#667085; font-size:0.875rem; margin:0.2rem 0 0 0;'>{selected_prop.get('address', 'N/A')}, {selected_prop.get('city', '')} {selected_prop.get('state', '')} {selected_prop.get('postal_code', '')}, {selected_prop.get('country', '')}</p>",
                            unsafe_allow_html=True,
                        )
                    with c_status:
                        st.markdown(
                            f"<div style='text-align:right;'>{render_status_badge(selected_prop.get('status', 'active'))}</div>",
                            unsafe_allow_html=True,
                        )

                    render_divider("1rem")

                    # Metadata + Risk breakdown
                    m1, m2, m3, m4 = st.columns(4)
                    with m1:
                        st.markdown(f"**Asset Type:**<br>{selected_prop.get('property_type', 'Commercial')}", unsafe_allow_html=True)
                    with m2:
                        score_val = f"{risk.get('overall_score', 0):.0f} / 100" if risk else "Not Audited"
                        st.markdown(f"**Risk Score:**<br>{score_val}", unsafe_allow_html=True)
                    with m3:
                        risk_level = risk.get("risk_level", "low") if risk else "low"
                        badge_html = render_status_badge(risk_level) if risk else "<span style='color:#94A3B8;'>—</span>"
                        st.markdown(f"**Risk Rating:**<br>{badge_html}", unsafe_allow_html=True)
                    with m4:
                        st.markdown(f"**Created:**<br>{selected_prop.get('created_at', '')[:10]}", unsafe_allow_html=True)

                # Recent Audits for Property
                render_section_header("Audit History", f"Audit sessions executed for {selected_prop['name']}")
                audits = _get_property_audits(prop_id)

                if audits:
                    for audit in audits[:4]:
                        with st.container(border=True):
                            ac1, ac2, ac3 = st.columns([2, 1, 1])
                            with ac1:
                                st.markdown(f"**{audit.get('audit_type', 'Deterministic Lease Audit')}**")
                                st.caption(f"Conducted on {audit.get('created_at', 'N/A')[:10]}")
                            with ac2:
                                st.markdown(f"Status: {render_status_badge(audit.get('status', 'resolved'))}", unsafe_allow_html=True)
                            with ac3:
                                st.markdown(f"**Total Billed:** {format_currency(audit.get('total_invoice_amount', 0))}")
                else:
                    render_empty_state("No Audits Run Yet", "Upload lease documents and invoice statements to run your first audit session.", "🔎")

                # Findings for Property
                render_section_header("Flagged Discrepancies", f"Contract discrepancies found in {selected_prop['name']}")
                findings = _get_property_findings(prop_id)

                if findings:
                    for f in findings[:6]:
                        with st.container(border=True):
                            fc1, fc2, fc3 = st.columns([2.5, 1, 1])
                            with fc1:
                                sev = (f.get("severity") or "low").lower()
                                st.markdown(
                                    f"{render_status_badge(sev)} <strong style='margin-left:0.5rem;'>{f.get('category', 'Finding').upper()}</strong>: {f.get('description', '')}",
                                    unsafe_allow_html=True,
                                )
                            with fc2:
                                st.markdown(f"Status: {render_status_badge(f.get('status', 'open'))}", unsafe_allow_html=True)
                            with fc3:
                                amt = float(f.get("amount", 0))
                                st.markdown(f"<span style='color:#16A34A; font-weight:700;'>{format_currency(amt)}</span>", unsafe_allow_html=True)
                else:
                    render_empty_state("No Findings On File", "This property currently has zero detected billing discrepancies.", "✅")

    # -----------------------------------------------------------------------
    # TAB 2: ADD PROPERTY
    # -----------------------------------------------------------------------
    with tab_add:
        render_section_header("Create New Commercial Asset", "Register a property into the portfolio management workspace")

        with st.form("create_property_form", clear_on_submit=False):
            col_name, col_type = st.columns([2, 1])
            with col_name:
                name = st.text_input("Property Name*", placeholder="e.g., Riverside Plaza Tower A")
            with col_type:
                prop_type = st.selectbox("Property Type*", ["Office", "Retail", "Industrial", "Multifamily", "Mixed-Use", "Other"])

            address = st.text_input("Street Address", placeholder="e.g., 100 Financial Center Blvd, Suite 400")

            c_city, c_state, c_zip, c_country = st.columns(4)
            with c_city:
                city = st.text_input("City", placeholder="New York")
            with c_state:
                state = st.text_input("State / Province", placeholder="NY")
            with c_zip:
                postal_code = st.text_input("Postal Code", placeholder="10001")
            with c_country:
                country = st.text_input("Country", value="USA")

            submitted = st.form_submit_button("Create Property Asset", type="primary")

            if submitted:
                if name.strip():
                    try:
                        _create_property(name, address, city, state, postal_code, country, prop_type)
                        render_alert(f"Property '{name}' created successfully!", kind="success", title="Success")
                        st.rerun()
                    except Exception as e:
                        render_alert(f"Error creating property: {str(e)}", kind="error", title="Creation Error")
                else:
                    render_alert("Property name is required.", kind="error", title="Validation Error")
