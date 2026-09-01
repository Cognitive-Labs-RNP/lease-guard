from __future__ import annotations

from typing import Any, Dict, List, Optional


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _finding(
    *,
    category: str,
    severity: str,
    billed_amount: float,
    allowed_amount: float,
    potential_recovery: float,
    explanation: str,
    lease_evidence: Optional[Dict[str, Any]] = None,
    invoice_evidence: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "category": category,
        "severity": severity,
        "billed_amount": round(billed_amount, 2),
        "allowed_amount": round(allowed_amount, 2),
        "potential_recovery": round(potential_recovery, 2),
        "explanation": explanation,
        "lease_evidence": lease_evidence or {},
        "invoice_evidence": invoice_evidence or {},
    }


def _allowed_cam_amount(lease: Dict[str, Any], invoice: Dict[str, Any]) -> float:
    base_rent = _to_float(lease.get("base_rent"), 0.0)
    cam_cap_pct = _to_float(lease.get("cam_cap_pct"), 0.0)
    tenant_share = _to_float(lease.get("tenant_share_pct"), 0.0)
    invoice_cam = _to_float(invoice.get("cam_expense"), 0.0)

    if base_rent <= 0:
        return 0.0
    max_cam = base_rent * cam_cap_pct
    allowed = max_cam * tenant_share
    return min(invoice_cam, allowed)


def _check_cam_cap(lease: Dict[str, Any], invoice: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    billed_amount = _to_float(invoice.get("cam_expense"), 0.0)
    allowed_amount = _allowed_cam_amount(lease, invoice)
    if billed_amount > allowed_amount + 0.01:
        findings.append(
            _finding(
                category="CAM cap",
                severity="high" if billed_amount - allowed_amount > 1000 else "medium",
                billed_amount=billed_amount,
                allowed_amount=allowed_amount,
                potential_recovery=max(billed_amount - allowed_amount, 0.0),
                explanation="CAM charge exceeds the lease cap allocation for the tenant share.",
                lease_evidence={
                    "base_rent": _to_float(lease.get("base_rent"), 0.0),
                    "cam_cap_pct": _to_float(lease.get("cam_cap_pct"), 0.0),
                    "tenant_share_pct": _to_float(lease.get("tenant_share_pct"), 0.0),
                },
                invoice_evidence={
                    "cam_expense": billed_amount,
                },
            )
        )
    return findings


def _check_excluded_expense(lease: Dict[str, Any], invoice: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    excluded = {str(item).strip().lower() for item in lease.get("excluded_expenses", [])}
    line_items = invoice.get("line_items") or []

    for item in line_items:
        category = str(item.get("category", "")).strip().lower()
        amount = _to_float(item.get("amount"), 0.0)
        if category in excluded and amount > 0:
            findings.append(
                _finding(
                    category="Excluded expense",
                    severity="high",
                    billed_amount=amount,
                    allowed_amount=0.0,
                    potential_recovery=amount,
                    explanation=f"The invoice line item '{item.get('category', '')}' is excluded by the lease terms.",
                    lease_evidence={"excluded_expenses": list(excluded)},
                    invoice_evidence={"category": item.get("category"), "amount": amount},
                )
            )
    return findings


def _check_rent_escalation(lease: Dict[str, Any], invoice: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    base_rent = _to_float(lease.get("base_rent"), 0.0)
    annual_increase = _to_float(lease.get("annual_increase_pct"), 0.0)
    current_rent = _to_float(lease.get("current_rent"), base_rent)
    billed_rent = _to_float(invoice.get("rent_amount"), 0.0)

    allowed_rent = current_rent * (1 + annual_increase)
    if billed_rent > allowed_rent + 0.01:
        findings.append(
            _finding(
                category="Rent escalation",
                severity="medium" if billed_rent - allowed_rent <= 1000 else "high",
                billed_amount=billed_rent,
                allowed_amount=allowed_rent,
                potential_recovery=max(billed_rent - allowed_rent, 0.0),
                explanation="Rent exceeds the lease-authorized annual escalation threshold.",
                lease_evidence={
                    "base_rent": base_rent,
                    "annual_increase_pct": annual_increase,
                    "current_rent": current_rent,
                },
                invoice_evidence={"rent_amount": billed_rent},
            )
        )
    return findings


def _check_administrative_fee(lease: Dict[str, Any], invoice: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    admin_fee_pct = _to_float(lease.get("admin_fee_pct"), 0.0)
    max_admin_fee = _to_float(lease.get("max_admin_fee_amount"), 0.0)
    billed_admin_fee = _to_float(invoice.get("admin_fee_amount"), 0.0)
    allowed_admin = max_admin_fee if max_admin_fee > 0 else 0.0

    if admin_fee_pct > 0:
        allowed_admin = max_admin_fee if max_admin_fee > 0 else (lease.get("base_rent", 0) or 0) * admin_fee_pct

    if billed_admin_fee > allowed_admin + 0.01:
        findings.append(
            _finding(
                category="Administrative fee",
                severity="medium",
                billed_amount=billed_admin_fee,
                allowed_amount=allowed_admin,
                potential_recovery=max(billed_admin_fee - allowed_admin, 0.0),
                explanation="Administrative fee exceeds the lease allowance.",
                lease_evidence={"admin_fee_pct": admin_fee_pct, "max_admin_fee_amount": max_admin_fee},
                invoice_evidence={"admin_fee_amount": billed_admin_fee},
            )
        )
    return findings


def _check_tenant_share(lease: Dict[str, Any], invoice: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    lease_share = _to_float(lease.get("tenant_share_pct"), 0.0)
    invoice_share = _to_float(invoice.get("tenant_share_pct"), lease_share)
    billed_amount = _to_float(invoice.get("total_amount"), 0.0)

    if invoice_share < lease_share - 0.01:
        findings.append(
            _finding(
                category="Tenant-share calculation",
                severity="medium",
                billed_amount=billed_amount,
                allowed_amount=billed_amount * (lease_share / max(invoice_share, 0.0001)),
                potential_recovery=max(billed_amount * (lease_share - invoice_share), 0.0),
                explanation="Tenant share applied on the invoice differs from the lease tenant-share percentage.",
                lease_evidence={"tenant_share_pct": lease_share},
                invoice_evidence={"tenant_share_pct": invoice_share, "total_amount": billed_amount},
            )
        )
    return findings


def audit_lease_invoice(lease: Dict[str, Any], invoice: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    findings.extend(_check_cam_cap(lease, invoice))
    findings.extend(_check_administrative_fee(lease, invoice))
    findings.extend(_check_excluded_expense(lease, invoice))
    findings.extend(_check_rent_escalation(lease, invoice))
    findings.extend(_check_tenant_share(lease, invoice))
    return findings
