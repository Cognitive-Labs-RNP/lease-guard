"""
LeaseGuard AI - Enterprise Lease Audit Platform

Main application entry point with sidebar navigation and page routing.
"""

import os

import streamlit as st
from dotenv import load_dotenv

from services.auth import get_current_user, login_user, logout_user, register_user
from services.demo import is_demo_mode
from ui.custom_theme import apply_custom_theme

load_dotenv()

st.set_page_config(
    page_title="LeaseGuard AI",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom theme
apply_custom_theme()


def show_auth_screen() -> None:
    """Display authentication screen."""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("# 🏢 LeaseGuard AI")
        st.markdown("Enterprise Lease Audit Platform")
        st.markdown("---")

        tab_login, tab_register = st.tabs(["Login", "Register"])

        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="user@example.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True, type="primary")

                if submitted:
                    result = login_user(email, password)
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])

        with tab_register:
            with st.form("register_form"):
                email = st.text_input("Email", placeholder="user@example.com", key="register_email")
                password = st.text_input("Password", type="password", key="register_password")
                password_confirmation = st.text_input("Confirm password", type="password", key="register_password_confirmation")
                submitted = st.form_submit_button("Register", use_container_width=True, type="primary")

                if submitted:
                    if password != password_confirmation:
                        st.error("Passwords do not match.")
                    else:
                        result = register_user(email, password)
                        if result["success"]:
                            st.success(result["message"])
                        else:
                            st.error(result["message"])


def show_dashboard() -> None:
    """Display main dashboard with sidebar navigation."""
    # Sidebar
    with st.sidebar:
        st.markdown("# 🏢 LeaseGuard AI")
        st.caption("v1.0.0 - Phase 7")

        # Demo mode indicator
        if is_demo_mode():
            st.warning("🎭 DEMO DATA — NOT REAL ANALYSIS", icon="⚠️")

        st.markdown("---")

        # Navigation
        st.markdown("### Navigation")

        page = st.radio(
            "Select page",
            options=[
                "Dashboard",
                "Properties",
                "Documents",
                "Audits",
                "Findings",
                "Risk Analysis",
                "Recovery",
                "Disputes",
                "Analytics",
                "Settings",
            ],
            key="page_nav",
            label_visibility="collapsed",
        )

        st.markdown("---")

        # User info
        st.markdown("### Account")
        user = get_current_user()
        if user is not None:
            email = getattr(user, "email", "User")
            st.write(f"📧 {email}")

        # Logout
        if st.button("Logout", use_container_width=True, type="secondary"):
            logout_user()
            st.rerun()

    # Page routing
    if page == "Dashboard":
        from pages import dashboard
        dashboard.render()

    elif page == "Properties":
        from pages import properties
        properties.render()

    elif page == "Documents":
        from pages import documents
        documents.render()

    elif page == "Audits":
        from pages import audits
        audits.render()

    elif page == "Findings":
        from pages import findings
        findings.render()

    elif page == "Risk Analysis":
        from pages import risk_analysis
        risk_analysis.render()

    elif page == "Recovery":
        from pages import recovery
        recovery.render()

    elif page == "Disputes":
        from pages import disputes
        disputes.render()

    elif page == "Analytics":
        from pages import analytics
        analytics.render()

    elif page == "Settings":
        from pages import settings
        settings.render()


# Main entry point
if get_current_user() is None:
    show_auth_screen()
else:
    show_dashboard()
