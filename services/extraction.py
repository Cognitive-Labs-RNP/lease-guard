"""
Document extraction service.

Provides synchronous wrappers for async RocketRide extraction pipelines.
Handles lease and invoice extraction with error handling and validation.
"""

import asyncio
import json
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv()


def _is_demo_mode() -> bool:
    """Check if demo mode is enabled."""
    return os.getenv("DEMO_MODE", "false").lower() == "true"


def extract_lease_data(text: str) -> Dict[str, Any]:
    """
    Extract lease data from text using RocketRide pipeline.

    Synchronous wrapper around async RocketRide extraction.
    Returns structured lease data on success.
    Raises RuntimeError with descriptive message on failure.

    Args:
        text: Raw lease document text

    Returns:
        Dict with extracted lease data:
        {
            "base_rent": float,
            "cam_cap_pct": float,
            "tenant_share_pct": float,
            "annual_increase_pct": float,
            "excluded_expenses": list[str],
            "lease_terms": Optional[Dict],
            "extraction_confidence": float (0-1),
            "status": "success" | "partial" | "error"
        }

    Raises:
        RuntimeError: If extraction fails, with one of:
        - "No LLM provider configured"
        - "Invalid or empty lease text"
        - "Extraction service unavailable"
        - "Malformed extraction response"
        - "Missing required lease fields"
    """
    if not text or not text.strip():
        raise RuntimeError("Invalid or empty lease text provided")

    try:
        from services.ai import extract_lease

        # Run async function in sync context
        result = asyncio.run(extract_lease(text))

        # Parse and validate result
        extracted = _parse_extraction_response(result, "lease")
        return extracted

    except ImportError:
        raise RuntimeError("RocketRide library not installed. Install via: pip install rocketride")
    except RuntimeError as e:
        # Re-raise RuntimeError with descriptive message
        if "No LLM provider" in str(e):
            raise RuntimeError(
                "No AI provider configured. Set ROCKETRIDE_GEMINI_KEY or "
                "(ROCKETRIDE_GROQ_KEY + ROCKETRIDE_GROQ_BASE_URL) in .env"
            )
        raise RuntimeError(f"Lease extraction failed: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected extraction error: {str(e)}")


def extract_invoice_data(text: str) -> Dict[str, Any]:
    """
    Extract invoice data from text.

    Currently uses the same lease extraction pipeline with invoice-specific prompting.
    Returns structured invoice data on success.

    Args:
        text: Raw invoice document text

    Returns:
        Dict with extracted invoice data:
        {
            "cam_expense": float,
            "rent_amount": float,
            "admin_fee_amount": float,
            "tax_amount": float,
            "total_amount": float,
            "tenant_share_pct": float,
            "invoice_terms": Optional[Dict],
            "extraction_confidence": float (0-1),
            "status": "success" | "partial" | "error"
        }

    Raises:
        RuntimeError: If extraction fails
    """
    if not text or not text.strip():
        raise RuntimeError("Invalid or empty invoice text provided")

    try:
        # For now, use lease extraction with invoice-specific prompt
        # In production, this would use a separate invoice extraction pipeline
        from services.ai import extract_lease

        # Run async function in sync context
        result = asyncio.run(extract_lease(text))

        # Parse and validate result as invoice
        extracted = _parse_extraction_response(result, "invoice")
        return extracted

    except ImportError:
        raise RuntimeError("RocketRide library not installed. Install via: pip install rocketride")
    except RuntimeError as e:
        if "No LLM provider" in str(e):
            raise RuntimeError(
                "No AI provider configured. Set ROCKETRIDE_GEMINI_KEY or "
                "(ROCKETRIDE_GROQ_KEY + ROCKETRIDE_GROQ_BASE_URL) in .env"
            )
        raise RuntimeError(f"Invoice extraction failed: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected extraction error: {str(e)}")


def generate_dispute_draft(property_name: str, amount: float, recovery_status: str) -> str:
    """Generate a reviewable dispute draft through RocketRide; never invent a draft on failure."""
    prompt = (
        "Draft a concise commercial lease dispute letter. State that it is a draft for human review, "
        f"identify the property as {property_name}, the potential recovery as ${amount:,.2f}, and "
        f"the recovery status as {recovery_status}. Do not make legal conclusions or invent lease clauses."
    )
    try:
        from services.ai import extract_lease_with_question

        result = asyncio.run(extract_lease_with_question(prompt))
        answers = result.get("result", {}).get("answers", [])
        if not answers or not isinstance(answers[0], str) or not answers[0].strip():
            raise RuntimeError("RocketRide returned an incomplete dispute draft")
        return answers[0].strip()
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError("RocketRide could not generate a dispute draft. Check the AI configuration and try again.") from exc


def _parse_extraction_response(response: Dict[str, Any], doc_type: str) -> Dict[str, Any]:
    """
    Parse and validate RocketRide extraction response.

    Attempts to extract JSON from response and validate required fields.

    Args:
        response: Raw response from RocketRide
        doc_type: "lease" or "invoice"

    Returns:
        Validated extraction result

    Raises:
        RuntimeError: If response is malformed or missing required fields
    """
    if not response:
        raise RuntimeError("Empty extraction response")

    try:
        # Extract the actual result from response wrapper
        if isinstance(response, dict) and "result" in response:
            result = response["result"]
        else:
            result = response

        # Try to get answers from response
        if isinstance(result, dict) and "answers" in result:
            answers = result["answers"]
        else:
            raise RuntimeError("No answers in extraction response")

        # answers is typically a list; get the first answer
        if not answers or not isinstance(answers, list) or len(answers) == 0:
            raise RuntimeError("No valid answers in extraction response")

        answer_text = answers[0]

        # Try to parse as JSON
        if isinstance(answer_text, str):
            try:
                # Remove markdown code blocks if present
                answer_text = answer_text.strip()
                if answer_text.startswith("```"):
                    answer_text = answer_text.split("```")[1]
                    if answer_text.startswith("json"):
                        answer_text = answer_text[4:]
                    answer_text = answer_text.strip()

                data = json.loads(answer_text)
            except json.JSONDecodeError:
                raise RuntimeError(f"Malformed JSON in extraction response: {answer_text[:100]}")
        else:
            data = answer_text

        if not isinstance(data, dict):
            raise RuntimeError("Extraction response must contain a JSON object")

        # Validate required fields based on document type
        if doc_type == "lease":
            required = ["base_rent"]
            for field in required:
                if field not in data or data[field] is None:
                    raise RuntimeError(f"Missing required lease field: {field}")

            return {
                "base_rent": float(data.get("base_rent", 0)),
                "cam_cap_pct": float(data.get("cam_cap_pct", 0.05)),
                "tenant_share_pct": float(data.get("tenant_share_pct", 0.25)),
                "annual_increase_pct": float(data.get("annual_increase_pct", 0.03)),
                "excluded_expenses": data.get("excluded_expenses", []),
                "lease_terms": data,
                "extraction_confidence": 0.8,  # Placeholder
                "status": "success",
            }

        elif doc_type == "invoice":
            required = ["cam_expense", "rent_amount"]
            for field in required:
                if field not in data or data[field] is None:
                    raise RuntimeError(f"Missing required invoice field: {field}")

            return {
                "cam_expense": float(data.get("cam_expense", 0)),
                "rent_amount": float(data.get("rent_amount", 0)),
                "admin_fee_amount": float(data.get("admin_fee_amount", 0)),
                "tax_amount": float(data.get("tax_amount", 0)),
                "total_amount": float(data.get("total_amount", 0)),
                "tenant_share_pct": float(data.get("tenant_share_pct", 0.25)),
                "invoice_terms": data,
                "extraction_confidence": 0.8,  # Placeholder
                "status": "success",
            }

        raise RuntimeError(f"Unknown document type: {doc_type}")

    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Error parsing extraction response: {str(e)}")


def get_sample_lease_data() -> Dict[str, Any]:
    """Get sample lease data for demo mode."""
    return {
        "base_rent": 120000.0,
        "cam_cap_pct": 0.05,
        "tenant_share_pct": 0.25,
        "annual_increase_pct": 0.03,
        "excluded_expenses": ["management_fee"],
        "lease_terms": {
            "lessor": "Sample Properties LLC",
            "lessee": "Demo Tenant Corp",
            "lease_start": "2020-01-01",
            "lease_end": "2025-12-31",
            "lease_type": "Triple Net",
        },
        "extraction_confidence": 1.0,
        "status": "success",
    }


def get_sample_invoice_data() -> Dict[str, Any]:
    """Get sample invoice data for demo mode."""
    return {
        "cam_expense": 1500.0,
        "rent_amount": 10000.0,
        "admin_fee_amount": 500.0,
        "tax_amount": 250.0,
        "total_amount": 12250.0,
        "tenant_share_pct": 0.25,
        "invoice_terms": {
            "invoice_number": "INV-2024-001",
            "invoice_date": "2024-09-01",
            "due_date": "2024-09-15",
            "billing_period": "2024-09",
        },
        "extraction_confidence": 1.0,
        "status": "success",
    }
