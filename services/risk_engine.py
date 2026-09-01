from __future__ import annotations

from typing import Any, Dict, List


def calculate_risk_score(category_scores: Dict[str, Any]) -> Dict[str, Any]:
    score_map = {
        "CAM risk": float(category_scores.get("cam_risk", 0)),
        "Rent escalation risk": float(category_scores.get("rent_escalation_risk", 0)),
        "Administrative fee risk": float(category_scores.get("administrative_fee_risk", 0)),
        "Tax risk": float(category_scores.get("tax_risk", 0)),
        "Audit rights risk": float(category_scores.get("audit_rights_risk", 0)),
    }

    overall_score = round(sum(score_map.values()) / max(len(score_map), 1), 2)

    if overall_score >= 80:
        risk_level = "critical"
    elif overall_score >= 60:
        risk_level = "high"
    elif overall_score >= 35:
        risk_level = "moderate"
    else:
        risk_level = "low"

    return {
        "overall_score": overall_score,
        "risk_level": risk_level,
        "category_scores": {
            "CAM risk": round(score_map["CAM risk"], 2),
            "Rent escalation risk": round(score_map["Rent escalation risk"], 2),
            "Administrative fee risk": round(score_map["Administrative fee risk"], 2),
            "Tax risk": round(score_map["Tax risk"], 2),
            "Audit rights risk": round(score_map["Audit rights risk"], 2),
        },
    }
