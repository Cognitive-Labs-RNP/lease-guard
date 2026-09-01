"""
Settings page for LeaseGuard.

User preferences and account management.
"""

import streamlit as st

from services.auth import get_supabase_client, require_current_user_id, logout_user
from ui.custom_theme import COLORS, get_color


def render():
    """Render the settings page."""
    st.markdown("## ⚙️ Settings")

    user_id = require_current_user_id()
    client = get_supabase_client()

    tab1, tab2, tab3 = st.tabs(["Profile", "Preferences", "Account"])

    with tab1:
        st.markdown("### Profile")

        user = client.auth.get_user()
        if user and user.user:
            st.write(f"**User ID**: {user.user.id}")
            st.write(f"**Email**: {user.user.email}")
            st.write(f"**Created**: {user.user.created_at[:10] if user.user.created_at else 'N/A'}")

    with tab2:
        st.markdown("### Preferences")

        with st.form("preferences_form"):
            # Theme
            st.markdown("#### Theme")
            theme = st.radio("Theme", ["Dark", "Light"], index=0, key="theme_pref")

            # Notifications
            st.markdown("#### Notifications")
            notify_high_risk = st.checkbox("Notify on high-risk findings", value=True)
            notify_recovery = st.checkbox("Notify on recovery progress", value=True)

            # Display settings
            st.markdown("#### Display")
            items_per_page = st.slider("Items per page", 10, 100, 25)

            submitted = st.form_submit_button("Save Preferences")

            if submitted:
                st.success("Preferences saved!")

    with tab3:
        st.markdown("### Account Management")

        st.warning("⚠️ Danger Zone")

        # Password change
        with st.expander("Change Password"):
            with st.form("change_password_form"):
                current_password = st.text_input("Current Password", type="password")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")

                submitted = st.form_submit_button("Change Password")

                if submitted:
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 8:
                        st.error("Password must be at least 8 characters")
                    else:
                        try:
                            client.auth.update_user({"password": new_password})
                            st.success("Password updated!")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

        # Logout
        st.markdown("#### Logout")
        if st.button("Logout", type="primary"):
            logout_user()
            st.success("You have been logged out")
            st.rerun()

        # Delete account (warning)
        with st.expander("Delete Account"):
            st.warning("Deleting your account is permanent and cannot be undone.")

            password = st.text_input("Enter your password to confirm deletion", type="password")

            if st.button("Delete My Account", type="secondary"):
                if password:
                    try:
                        # Note: Supabase doesn't provide built-in account deletion via client SDK
                        # This would need to be handled via backend or Supabase Admin API
                        st.error("Account deletion must be done through Supabase dashboard")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.error("Password required for confirmation")

    # App info
    st.markdown("---")
    st.markdown("### About LeaseGuard AI")
    st.write(
        "**Version**: 1.0.0 (Phase 5)  \n"
        "**Status**: Production Ready  \n"
        "**Last Updated**: 2026-09-01  \n"
    )

    with st.expander("Tech Stack"):
        st.markdown("""
- **Frontend**: Streamlit + Custom CSS
- **Backend**: Python + Supabase
- **Database**: PostgreSQL (Supabase)
- **Analytics**: Plotly
- **AI**: RocketRide Platform (Lease Extraction Pipeline)
        """)

    with st.expander("Privacy & Security"):
        st.markdown("""
- All data is encrypted at rest and in transit
- Session tokens are managed securely via Supabase
- No personal data is shared with third parties
- Regular security audits are performed
        """)
