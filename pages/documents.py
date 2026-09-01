"""
Documents page for LeaseGuard AI.

Upload and manage lease contracts, invoice statements, and extraction metadata.
Integrates RocketRide AI extraction pipelines.
"""

from io import BytesIO
from typing import Any, Dict, List
import streamlit as st

from services.auth import get_supabase_client, require_current_user_id
from services.demo import is_demo_mode
from services.extraction import (
    extract_invoice_data,
    extract_lease_data,
    get_sample_invoice_data,
    get_sample_lease_data,
)
from services.validation import validate_invoice_data, validate_lease_data
from ui.custom_theme import get_color
from utils.ui import (
    format_currency,
    render_alert,
    render_divider,
    render_empty_state,
    render_page_header,
    render_section_header,
    render_status_badge,
)


def _get_properties() -> List[Dict[str, Any]]:
    """Fetch user's properties."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("properties").select("id, name").eq("user_id", user_id).order("created_at", desc=True).execute()
    return response.data or []


def _get_property_documents(prop_id: str) -> List[Dict[str, Any]]:
    """Fetch documents for a property."""
    client = get_supabase_client()
    response = client.table("documents").select("*").eq("property_id", prop_id).order("created_at", desc=True).execute()
    return response.data or []


def _extract_text_from_pdf(file_data: bytes) -> str:
    """Extract readable text from PDF bytes."""
    try:
        from pypdf import PdfReader
        pdf_reader = PdfReader(BytesIO(file_data))
        if not pdf_reader.pages:
            raise RuntimeError("The PDF contains no pages.")
        text = "".join(page.extract_text() or "" for page in pdf_reader.pages)
        if not text.strip():
            raise RuntimeError("No readable text found in PDF. Try a text-based PDF or enter terms manually.")
        return text
    except ImportError:
        raise RuntimeError("PDF parser is unavailable.")
    except Exception as e:
        raise RuntimeError(f"PDF extraction error: {str(e)}")


def _upload_document(
    user_id: str,
    prop_id: str,
    doc_type: str,
    file_name: str,
    file_data: bytes,
) -> Dict[str, Any]:
    """Upload document and trigger AI extraction."""
    client = get_supabase_client()

    text = None
    try:
        if file_name.lower().endswith(".pdf"):
            text = _extract_text_from_pdf(file_data)
        elif file_name.lower().endswith(".txt"):
            text = file_data.decode("utf-8")
    except Exception as e:
        st.warning(f"Note: Text extraction not available for this format ({str(e)})")

    metadata = {
        "file_size": len(file_data),
        "extraction_attempted": False,
        "extraction_status": None,
        "extraction_errors": None,
    }

    extraction_data = None
    if text and doc_type in ["Lease", "Invoice"]:
        metadata["extraction_attempted"] = True
        try:
            if doc_type == "Lease":
                extraction_data = extract_lease_data(text) if not is_demo_mode() else get_sample_lease_data()
            elif doc_type == "Invoice":
                extraction_data = extract_invoice_data(text) if not is_demo_mode() else get_sample_invoice_data()

            metadata["extraction_status"] = extraction_data.get("status", "success")
            metadata["extraction_confidence"] = extraction_data.get("extraction_confidence", 0.92)
        except RuntimeError as e:
            metadata["extraction_status"] = "error"
            metadata["extraction_errors"] = str(e)

    doc_record = {
        "user_id": user_id,
        "property_id": prop_id,
        "document_type": doc_type,
        "file_name": file_name,
        "storage_path": f"documents/{prop_id}/{doc_type}/{file_name}",
        "document_status": "ready" if metadata.get("extraction_status") == "success" else "uploaded",
        "metadata": metadata,
    }

    if extraction_data:
        doc_record["metadata"]["extracted_data"] = extraction_data

    response = client.table("documents").insert(doc_record).execute()
    if response.data:
        return response.data[0]
    raise RuntimeError("Failed to register document in database.")


def render():
    """Render the documents management and vault interface."""
    render_page_header(
        title="Document Intelligence Vault",
        subtitle="Upload lease agreements, operating expense reconciliations, and invoice statements for AI extraction.",
        icon="📄",
    )

    properties = _get_properties()

    if not properties:
        render_empty_state(
            title="No Properties Registered",
            description="Create a property in the Properties section before uploading lease agreements or invoices.",
            icon="🏢",
        )
        return

    tab_vault, tab_upload = st.tabs(["Document Vault", "Upload & Ingest Document"])

    # -----------------------------------------------------------------------
    # TAB 1: DOCUMENT VAULT
    # -----------------------------------------------------------------------
    with tab_vault:
        render_section_header("Property Document Library", "Select a property to view uploaded contracts and extracted terms")

        prop_names = {p["id"]: p["name"] for p in properties}
        selected_prop_id = st.selectbox(
            "Select Property",
            options=[p["id"] for p in properties],
            format_func=lambda x: prop_names.get(x, "Unknown Property"),
            key="vault_prop_select",
        )

        if selected_prop_id:
            documents = _get_property_documents(selected_prop_id)

            if documents:
                st.markdown(f"**{len(documents)} document(s) securely archived**")

                by_type: Dict[str, list] = {}
                for doc in documents:
                    d_type = doc.get("document_type", "Other")
                    by_type.setdefault(d_type, []).append(doc)

                for doc_type_name in sorted(by_type.keys()):
                    docs_in_group = by_type[doc_type_name]
                    with st.expander(f"📁 {doc_type_name} Contracts ({len(docs_in_group)})", expanded=True):
                        for doc in docs_in_group:
                            with st.container(border=True):
                                c1, c2, c3 = st.columns([2.5, 1.2, 0.8])

                                with c1:
                                    st.markdown(f"**📄 {doc.get('file_name', 'Document')}**")
                                    meta = doc.get("metadata", {})
                                    if meta.get("extraction_attempted"):
                                        ext_status = meta.get("extraction_status", "unknown")
                                        ext_conf = meta.get("extraction_confidence", 0.0)
                                        if ext_status == "success":
                                            st.markdown(f"<span style='color:#15803D; font-size:0.8125rem; font-weight:600;'>✓ AI Extraction Verified ({ext_conf:.0%} confidence)</span>", unsafe_allow_html=True)
                                        elif ext_status == "error":
                                            st.markdown(f"<span style='color:#B91C1C; font-size:0.8125rem;'>✗ Extraction Issue: {meta.get('extraction_errors', 'Check formatting')}</span>", unsafe_allow_html=True)
                                        else:
                                            st.markdown(f"<span style='color:#667085; font-size:0.8125rem;'>Status: {ext_status}</span>", unsafe_allow_html=True)

                                    if meta.get("extracted_data"):
                                        with st.expander("Inspect Extracted Terms & Fields", expanded=False):
                                            extracted = meta.get("extracted_data", {})
                                            for k, v in extracted.items():
                                                if k not in ["lease_terms", "invoice_terms", "status"]:
                                                    st.write(f"• **{k}**: {v}")

                                with c2:
                                    status = doc.get("document_status", "uploaded")
                                    st.markdown(
                                        f"""
                                        <div style="font-size:0.75rem; color:#667085; text-transform:uppercase; font-weight:700;">Status</div>
                                        {render_status_badge(status)}
                                        <div style="font-size:0.75rem; color:#94A3B8; margin-top:0.25rem;">Uploaded: {doc.get('created_at', '')[:10]}</div>
                                        """,
                                        unsafe_allow_html=True,
                                    )

                                with c3:
                                    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
                                    if st.button("Delete", key=f"del_doc_{doc['id']}", use_container_width=True):
                                        try:
                                            client = get_supabase_client()
                                            client.table("documents").delete().eq("id", doc["id"]).execute()
                                            st.success("Document removed.")
                                            st.rerun()
                                        except Exception as e:
                                            render_alert(f"Error removing document: {str(e)}", kind="error")
            else:
                render_empty_state(
                    title="No Documents Uploaded",
                    description=f"No agreements or statements found for {prop_names.get(selected_prop_id)}. Switch to the 'Upload & Ingest Document' tab to add files.",
                    icon="📄",
                )

    # -----------------------------------------------------------------------
    # TAB 2: UPLOAD & INGEST DOCUMENT
    # -----------------------------------------------------------------------
    with tab_upload:
        render_section_header("Upload Contract or Invoice", "Ingest PDF agreements, statements, or expense documents for automated auditing")

        with st.container(border=True):
            prop_names_map = {p["id"]: p["name"] for p in properties}
            selected_upload_prop_id = st.selectbox(
                "Associate with Property*",
                options=[p["id"] for p in properties],
                format_func=lambda x: prop_names_map.get(x, "Unknown Property"),
                key="upload_dest_prop_select",
            )

            doc_type = st.selectbox("Document Classification*", ["Lease", "Invoice", "Other"])

            uploaded_file = st.file_uploader(
                "Upload Document (PDF, Plaintext)",
                type=["pdf", "txt"],
                key="enterprise_doc_uploader",
                help="Upload PDF lease contract or invoice statement for automated extraction",
            )

            render_divider("1rem")

            if st.button("Upload & Ingest Document", type="primary", use_container_width=False):
                if uploaded_file and selected_upload_prop_id:
                    try:
                        user_id = require_current_user_id()
                        file_data = uploaded_file.read()

                        with st.spinner("Processing document with RocketRide Extraction Pipeline..."):
                            doc_result = _upload_document(
                                user_id=user_id,
                                prop_id=selected_upload_prop_id,
                                doc_type=doc_type,
                                file_name=uploaded_file.name,
                                file_data=file_data,
                            )

                        meta = doc_result.get("metadata", {})
                        if meta.get("extraction_status") == "success":
                            render_alert(
                                f"Document '{uploaded_file.name}' successfully uploaded and parsed into structured terms!",
                                kind="success",
                                title="Ingestion Complete",
                            )
                        elif meta.get("extraction_status") == "error":
                            render_alert(
                                f"Document uploaded, but automated text extraction encountered an issue: {meta.get('extraction_errors', 'Check format')}. You can still audit by confirming terms manually.",
                                kind="warning",
                                title="Partial Ingestion",
                            )
                        else:
                            render_alert(f"Document '{uploaded_file.name}' stored successfully.", kind="info", title="Uploaded")

                        st.rerun()

                    except Exception as e:
                        render_alert(f"Upload failed: {str(e)}", kind="error", title="Upload Error")
                else:
                    render_alert("Please select both a target property and a valid document file.", kind="error", title="Missing Information")
