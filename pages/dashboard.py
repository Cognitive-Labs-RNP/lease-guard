import streamlit as st

st.title("Dashboard")
st.caption("Portfolio overview for the LeaseGuard AI foundation")

st.markdown("This dashboard placeholder is ready for future lease, invoice, and recovery metrics.")

metrics = [
    ("Portfolio properties", "0", "No properties yet"),
    ("Active audits", "0", "Awaiting data"),
    ("Potential recovery", "$0", "Not calculated yet"),
    ("Risk score", "0/100", "Baseline placeholder"),
]

columns = st.columns(4)
for column, (label, value, help_text) in zip(columns, metrics):
    column.metric(label, value, help_text)

st.subheader("Recent activity")
st.info("No lease or invoice data has been connected yet. This is intentionally a placeholder for Phase 1.")
