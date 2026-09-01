"""
Documents page for LeaseGuard.

Upload and manage lease and invoice documents.
Integrates document extraction via RocketRide pipelines.
"""

from io import BytesIO
from typing import Any, Dict

import streamlit as st

from services.auth import get_supabase_client, require_current_user_id
from services.extraction import extract_lease_data, extract_invoice_data, get_sample_lease_data, get_sample_invoice_data
from services.validation import validate_lease_data, validate_invoice_data
from services.demo import is_demo_mode
from ui.custom_theme import get_color


def _get_properties() -> list[Dict[str, Any]]:
    """Fetch user's properties."""
    user_id = require_current_user_id()
    client = get_supabase_client()
    response = client.table("properties").select("id, name").eq("user_id", user_id).order("created_at", desc=True).execute()
    return response.data or []


def _get_property_documents(prop_id: str) -> list[Dict[str, Any]]:
    """Fetch documents for a property."""
    client = get_supabase_client()
    response = client.table("documents").select("*").eq("property_id", prop_id).order("created_at", desc=True).execute()
    return response.data or []


def _upload_document(
    user_id: str,
    prop_id: str,
    doc_type: str,
    file_name: str,
    file_data: bytes,
) -> Dict[str, Any]:
    """
    Upload a document and trigger extraction.

    Args:
        user_id: User ID
        prop_id: Property ID
        doc_type: Document type (Lease, Invoice, Other)
        file_name: Original file name
        file_data: File content as bytes

    Returns:
        Document record with metadata and extraction results

    Raises:
        RuntimeError: If upload or extraction fails
    """
    client = get_supabase_client()

    try:
        # Try to extract text from file
        try:
            # For PDF/text files, attempt to extract as text
            if file_name.lower().endswith(".pdf"):
                text = _extract_text_from_pdf(file_data)
            elif file_name.lower().endswith(".txt"):
                text = file_data.decode("utf-8")
            else:
                # For images, would need OCR - for now, skip extraction
                text = None
        except Exception as e:
            st.warning(f"Could not extract text from file: {str(e)}")
            text = None

        # Initialize metadata
        metadata = {
            "file_size": len(file_data),
            "extraction_attempted": False,
            "extraction_status": None,
            "extraction_errors": None,
        }

        # Attempt extraction if we have text
        extraction_data = None
        if text and doc_type in ["Lease", "Invoice"]:
            metadata["extraction_attempted"] = True

            try:
                if doc_type == "Lease":
                    extraction_data = extract_lease_data(text) if not is_demo_mode() else get_sample_lease_data()
                    metadata["extraction_status"] = extraction_data.get("status", "unknown")
                    metadata["extraction_confidence"] = extraction_data.get("extraction_confidence", 0)
                elif doc_type == "Invoice":
                    extraction_data = extract_invoice_data(text) if not is_demo_mode() else get_sample_invoice_data()
                    metadata["extraction_status"] = extraction_data.get("status", "unknown")
                    metadata["extraction_confidence"] = extraction_data.get("extraction_confidence", 0)
            except RuntimeError as e:
                metadata["extraction_status"] = "error"
                metadata["extraction_errors"] = str(e)
                # Don't fail the upload if extraction fails - still save the document

        # Store document record in database
        doc_record = {
            "user_id": user_id,
            "property_id": prop_id,
            "document_type": doc_type,
            "file_name": file_name,
            "storage_path": f"documents/{prop_id}/{doc_type}/{file_name}",
            "document_status": "ready" if metadata["extraction_status"] == "success" else "uploaded",
            "metadata": metadata,
        }

        if extraction_data:
            doc_record["metadata"]["extracted_data"] = extraction_data

        response = client.table("documents").insert(doc_record).execute()
        if response.data:
            return response.data[0]
        else:
            raise RuntimeError("Failed to insert document record")

    except Exception as e:
        raise RuntimeError(f"Error uploading document: {str(e)}")


def _extract_text_from_pdf(file_data: bytes) -> str:
    """
    Extract text from PDF file.

    Args:
        file_data: PDF file content as bytes

    Returns:
        Extracted text

    Raises:
        RuntimeError: If PDF extraction fails
    """
    try:
        from pypdf import PdfReader

        pdf_reader = PdfReader(BytesIO(file_data))
        if not pdf_reader.pages:
            raise RuntimeError("The PDF contains no pages")
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        if not text.strip():
            raise RuntimeError("No readable text was found. Upload a text-based PDF or enter the values manually.")
        return text
    except ImportError:
        raise RuntimeError("PDF support is unavailable. Reinstall dependencies with: pip install -r requirements.txt")
    except Exception as e:
        raise RuntimeError(f"PDF extraction failed: {str(e)}")


def render():
    """Render the documents page."""
    st.markdown("## 📄 Documents")

    if is_demo_mode():
        st.info("🎭 **DEMO MODE** — Using sample data for demonstration")

    properties = _get_properties()

    if not properties:
        st.info("No properties yet. Create a property first to upload documents.")
        return

    tab1, tab2 = st.tabs(["View Documents", "Upload Document"])

    with tab1:
        st.markdown("### Property Documents")

        prop_names = {p["id"]: p["name"] for p in properties}
        selected_prop_id = st.selectbox(
            "Select property",
            options=[p["id"] for p in properties],
            format_func=lambda x: prop_names.get(x, "Unknown"),
            key="view_prop_select"
        )

        if selected_prop_id:
            documents = _get_property_documents(selected_prop_id)

            if documents:
                st.markdown(f"**{len(documents)} documents**")

                # Group by type
                by_type = {}
                for doc in documents:
                    doc_type = doc.get("document_type", "Other")
                    if doc_type not in by_type:
                        by_type[doc_type] = []
                    by_type[doc_type].append(doc)

                for doc_type in sorted(by_type.keys()):
                    with st.expander(f"📑 {doc_type} ({len(by_type[doc_type])})"):
                        for doc in by_type[doc_type]:
                            col1, col2, col3 = st.columns([2, 1, 1])

                            with col1:
                                st.write(f"**{doc.get('file_name', 'N/A')}**")

                                # Show extraction metadata
                                meta = doc.get("metadata", {})
                                if meta.get("extraction_attempted"):
                                    ext_status = meta.get("extraction_status", "unknown")
                                    ext_conf = meta.get("extraction_confidence", 0)

                                    if ext_status == "success":
                                        st.caption(f"✓ Extraction successful ({ext_conf:.0%} confidence)")
                                    elif ext_status == "error":
                                        st.caption(f"✗ Extraction failed: {meta.get('extraction_errors', 'unknown error')}")
                                    else:
                                        st.caption(f"◐ Extraction: {ext_status}")

                                # Show extracted data if available
                                if meta.get("extracted_data"):
                                    with st.expander("View extracted data"):
                                        extracted = meta.get("extracted_data", {})
                                        # Show key fields
                                        for key, value in extracted.items():
                                            if key not in ["lease_terms", "invoice_terms", "status"]:
                                                st.write(f"• {key}: {value}")

                            with col2:
                                status = doc.get("document_status", "unknown")
                                status_emoji = (
                                    "🟢" if status == "ready"
                                    else "🟡" if status == "processing"
                                    else "🔴" if status == "error"
                                    else "⚪"
                                )
                                st.write(status_emoji)

                            with col3:
                                if st.button("Delete", key=f"delete_{doc['id']}"):
                                    try:
                                        client = get_supabase_client()
                                        client.table("documents").delete().eq("id", doc["id"]).execute()
                                        st.success("Document deleted")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
            else:
                st.info("No documents yet for this property")

    with tab2:
        st.markdown("### Upload Document")

        prop_names_list = {p["id"]: p["name"] for p in properties}
        selected_prop_id = st.selectbox(
            "Select property",
            options=[p["id"] for p in properties],
            format_func=lambda x: prop_names_list.get(x, "Unknown"),
            key="upload_prop_select"
        )

        doc_type = st.selectbox("Document Type", ["Lease", "Invoice", "Other"])

        uploaded_file = st.file_uploader(
            "Choose file (PDF, image, or text)",
            type=["pdf", "png", "jpg", "jpeg", "txt"],
            key="doc_uploader"
        )

        if st.button("Upload"):
            if uploaded_file and selected_prop_id:
                try:
                    user_id = require_current_user_id()
                    file_data = uploaded_file.read()

                    with st.spinner("Uploading and extracting document..."):
                        doc_result = _upload_document(
                            user_id=user_id,
                            prop_id=selected_prop_id,
                            doc_type=doc_type,
                            file_name=uploaded_file.name,
                            file_data=file_data
                        )

                        meta = doc_result.get("metadata", {})

                        if meta.get("extraction_status") == "success":
                            st.success(f"✓ Document '{uploaded_file.name}' uploaded and extracted successfully!")
                            if meta.get("extracted_data"):
                                st.write("**Extracted data preview:**")
                                extracted = meta.get("extracted_data", {})
                                for key, value in extracted.items():
                                    if key not in ["lease_terms", "invoice_terms", "status", "extraction_confidence"]:
                                        st.write(f"• {key}: {value}")
                        elif meta.get("extraction_status") == "error":
                            st.warning(
                                f"✓ Document uploaded but extraction failed:\n\n"
                                f"{meta.get('extraction_errors', 'Unknown error')}\n\n"
                                f"You can still run an audit by entering data manually."
                            )
                        else:
                            st.info(f"✓ Document '{uploaded_file.name}' uploaded successfully!")

                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error uploading document: {str(e)}")
                    st.info("Make sure you have a valid Supabase connection and API keys configured.")
            else:
                st.error("Please select a property and file")
