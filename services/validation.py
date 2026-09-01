"""
Data validation service.

Validates extracted lease and invoice data before audit processing.
Provides clear feedback on what's missing or invalid.
"""

from typing import Any, Dict, List, Tuple


def _number(value: Any, field: str, errors: List[str]) -> float | None:
    """Convert a user/AI value without allowing validation itself to crash."""
    try:
        return float(value)
    except (ValueError, TypeError):
        errors.append(f"{field} is not a valid number: {value}")
        return None


def validate_lease_data(lease: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate extracted lease data.

    Checks for required fields and reasonable values.

    Args:
        lease: Extracted lease data

    Returns:
        Tuple of (is_valid, error_messages)
        is_valid: True if data is valid, False if any issues
        error_messages: List of validation errors (empty if valid)
    """
    errors = []

    if not lease:
        return False, ["Lease data is empty"]

    # Check required fields
    required_fields = ["base_rent"]
    for field in required_fields:
        if field not in lease:
            errors.append(f"Missing required field: {field}")
        elif lease[field] is None:
            errors.append(f"Required field is None: {field}")

    # Check numeric fields
    base_rent = _number(lease.get("base_rent", 0), "Base rent", errors)
    if base_rent is not None:
        if base_rent < 0:
            errors.append("Base rent cannot be negative")
        if base_rent == 0:
            errors.append("Base rent is zero (likely extraction error)")

    # CAM cap percentage
    try:
        cam_cap = float(lease.get("cam_cap_pct", 0))
        if cam_cap < 0 or cam_cap > 1:
            errors.append(f"CAM cap percentage should be 0-1, got {cam_cap}")
    except (ValueError, TypeError):
        pass  # Optional field

    # Tenant share percentage
    try:
        tenant_share = float(lease.get("tenant_share_pct", 0))
        if tenant_share < 0 or tenant_share > 1:
            errors.append(f"Tenant share percentage should be 0-1, got {tenant_share}")
    except (ValueError, TypeError):
        pass  # Optional field

    # Annual increase percentage
    try:
        annual_increase = float(lease.get("annual_increase_pct", 0))
        if annual_increase < 0 or annual_increase > 1:
            errors.append(f"Annual increase percentage should be 0-1, got {annual_increase}")
    except (ValueError, TypeError):
        pass  # Optional field

    return len(errors) == 0, errors


def validate_invoice_data(invoice: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate extracted invoice data.

    Checks for required fields and reasonable values.

    Args:
        invoice: Extracted invoice data

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    if not invoice:
        return False, ["Invoice data is empty"]

    # Check required fields
    required_fields = ["cam_expense", "rent_amount"]
    for field in required_fields:
        if field not in invoice:
            errors.append(f"Missing required field: {field}")
        elif invoice[field] is None:
            errors.append(f"Required field is None: {field}")

    # Validate numeric fields
    numeric_fields = ["cam_expense", "rent_amount", "admin_fee_amount", "tax_amount", "total_amount"]
    for field in numeric_fields:
        if field in invoice:
            try:
                value = float(invoice.get(field, 0))
                if value < 0:
                    errors.append(f"{field} cannot be negative: {value}")
            except (ValueError, TypeError):
                errors.append(f"{field} is not a valid number: {invoice.get(field)}")

    # Tenant share percentage
    try:
        tenant_share = float(invoice.get("tenant_share_pct", 0))
        if tenant_share < 0 or tenant_share > 1:
            errors.append(f"Tenant share percentage should be 0-1, got {tenant_share}")
    except (ValueError, TypeError):
        pass  # Optional field

    # Check for zero amounts (possible extraction failure)
    rent = _number(invoice.get("rent_amount", 0), "rent_amount", errors)
    cam = _number(invoice.get("cam_expense", 0), "cam_expense", errors)
    if rent == 0 and cam == 0:
        errors.append("Both rent_amount and cam_expense are zero (likely extraction error)")

    return len(errors) == 0, errors


def validate_audit_ready(lease: Dict[str, Any], invoice: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check if lease and invoice data are ready for audit.

    Combines lease and invoice validation, and checks cross-field consistency.

    Args:
        lease: Extracted lease data
        invoice: Extracted invoice data

    Returns:
        Tuple of (is_ready, error_messages)
        is_ready: True if both documents are valid and consistent
        error_messages: List of all validation errors
    """
    all_errors = []

    # Validate each document
    lease_valid, lease_errors = validate_lease_data(lease)
    invoice_valid, invoice_errors = validate_invoice_data(invoice)

    all_errors.extend([f"Lease: {e}" for e in lease_errors])
    all_errors.extend([f"Invoice: {e}" for e in invoice_errors])

    # Cross-field checks (only if both are somewhat valid)
    if lease_valid and invoice_valid:
        base_rent = float(lease.get("base_rent", 0))
        rent_amount = float(invoice.get("rent_amount", 0))

        # Check if invoice rent amount is reasonable relative to lease
        if rent_amount > 0 and base_rent > 0:
            monthly_rent = base_rent / 12
            # Invoice rent should be within 50%-150% of monthly rent (allowing for variations)
            if rent_amount < monthly_rent * 0.5 or rent_amount > monthly_rent * 1.5:
                all_errors.append(
                    f"Invoice rent ({rent_amount}) seems inconsistent with "
                    f"monthly lease rent ({monthly_rent:.0f})"
                )

    return len(all_errors) == 0, all_errors


def extract_summary(errors: List[str]) -> str:
    """Create a user-friendly summary of validation errors."""
    if not errors:
        return "Data is valid and ready for audit."

    return (
        "**Data Validation Issues** (must be resolved before audit):\n\n"
        + "\n".join([f"• {e}" for e in errors])
    )
