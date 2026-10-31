from typing import Dict, Any, List
from datetime import datetime


def explanation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    decision = state.get("decision", {})
    signals = state.get("signals", [])
    specialist_results = state.get("specialist_results", {})
    input_data = state.get("input", {})

    risk_level = decision.get("risk_level", "UNKNOWN")
    risk_score = decision.get("risk_score", 0)
    final_decision = decision.get("decision", "UNKNOWN")
    decision_reason = decision.get("decision_reason", "")

    executive_summary = _generate_executive_summary(
        input_data, risk_level, risk_score, final_decision, decision_reason
    )

    evidence_trail = _build_evidence_trail(signals, specialist_results)
    confidence = _assess_confidence(signals, specialist_results)
    recommendations = _generate_recommendations(
        final_decision,
        risk_level,
        specialist_results,
        decision.get("contributing_factors", [])
    )

    state["explanation"] = {
        "timestamp": datetime.now().isoformat(),
        "executive_summary": executive_summary,
        "risk_assessment": {
            "score": risk_score,
            "level": risk_level,
            "decision": final_decision
        },
        "evidence_trail": evidence_trail,
        "confidence": confidence,
        "recommendations": recommendations,
        "full_narrative": _generate_full_narrative(
            input_data,
            executive_summary,
            evidence_trail,
            confidence,
            recommendations
        )
    }

    return state


def _generate_executive_summary(
    input_data: Dict[str, Any],
    risk_level: str,
    risk_score: float,
    decision: str,
    reason: str
) -> str:
    company = input_data.get("company", "Unknown")
    country = input_data.get("country", "Unknown")
    value = input_data.get("value", 0)

    return (
        f"Transaction involving {company} ({country}) valued at {value:,.0f}.\n"
        f"Decision: {decision}\n"
        f"Risk Level: {risk_level}\n"
        f"Risk Score: {risk_score:.1%}\n"
        f"{reason}"
    )


def _build_evidence_trail(
    signals: List[Dict[str, Any]],
    specialist_results: Dict[str, Any]
) -> List[Dict[str, Any]]:
    evidence = []

    for signal in signals:
        signal_type = signal.get("type", "unknown")
        for item in signal.get("evidence", []):
            evidence.append({
                "source": f"Swarm ({signal_type})",
                "type": item.get("type", "observation"),
                "finding": item.get("description", str(item)),
                "severity": item.get("severity", "INFO"),
                "score_impact": signal.get("score", 0)
            })

    sanctions = specialist_results.get("sanctions", {})
    if sanctions.get("verified"):
        for item in sanctions.get("evidence", []):
            evidence.append({
                "source": "Sanctions",
                "type": item.get("type", "verification"),
                "finding": item.get("entity") or item.get("country"),
                "severity": item.get("severity", "HIGH")
            })

    return evidence


def _assess_confidence(
    signals: List[Dict[str, Any]],
    specialist_results: Dict[str, Any]
) -> Dict[str, Any]:
    confidences = [s.get("confidence", 0.5) for s in signals]

    if specialist_results.get("sanctions", {}).get("verified"):
        confidences.append(0.95)

    avg = sum(confidences) / max(len(confidences), 1)

    if avg >= 0.8:
        level = "HIGH"
    elif avg >= 0.6:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "level": level,
        "score": round(avg, 2),
        "description": "Confidence derived from signal reliability"
    }


def _generate_recommendations(
    decision: str,
    risk_level: str,
    specialist_results: Dict[str, Any],
    contributing_factors: List[Dict[str, Any]]
) -> List[str]:
    recs = []

    if decision == "BLOCK":
        recs.append("Do not proceed with transaction")
        if specialist_results.get("sanctions", {}).get("hit"):
            recs.append("Escalate to compliance immediately")
        recs.append("Document for audit")

    elif decision == "FLAG":
        recs.append("Manual review required")
        recs.append("Request additional documentation")

    else:
        recs.append("Proceed with standard processing")
        if risk_level == "MEDIUM":
            recs.append("Apply enhanced monitoring")

    return list(dict.fromkeys(recs))


def _generate_full_narrative(
    input_data: Dict[str, Any],
    summary: str,
    evidence: List[Dict[str, Any]],
    confidence: Dict[str, Any],
    recommendations: List[str]
) -> str:
    lines = [
        "RISK ASSESSMENT REPORT",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        summary,
        "",
        "Evidence:"
    ]

    if evidence:
        for i, item in enumerate(evidence, 1):
            lines.append(
                f"{i}. [{item.get('severity')}] {item.get('finding')}"
            )
    else:
        lines.append("No significant risk indicators detected.")

    lines.extend([
        "",
        f"Confidence: {confidence.get('level')} ({confidence.get('score')})",
        "",
        "Recommendations:"
    ])

    for i, r in enumerate(recommendations, 1):
        lines.append(f"{i}. {r}")

    return "\n".join(lines)