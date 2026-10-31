from typing import Dict, Any, List
from memory.state import RISK_THRESHOLDS


def aggregator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    signals = state.get("signals", [])
    specialist_results = state.get("specialist_results", {})
    risk_factors = state.get("risk_factors", [])

    weighted_scores: List[Dict[str, Any]] = []
    contributing_factors: List[Dict[str, Any]] = []

    for signal in signals:
        signal_type = signal.get("type", "unknown")
        score = float(signal.get("score", 0.0))
        confidence = float(signal.get("confidence", 0.5))

        weighted_score = score * confidence

        weighted_scores.append({
            "source": f"swarm_{signal_type}",
            "raw_score": score,
            "confidence": confidence,
            "weighted_score": weighted_score
        })

        if score > 0.3:
            for evidence in signal.get("evidence", []):
                contributing_factors.append({
                    "source": signal_type,
                    "factor": evidence.get("description", evidence.get("type", "Unknown")),
                    "severity": evidence.get("severity", "MEDIUM"),
                    "score_contribution": weighted_score
                })

    sanctions = specialist_results.get("sanctions", {})

    if sanctions.get("verified"):
        if sanctions.get("company_hit"):
            weighted_scores.append({
                "source": "specialist_sanctions_company",
                "raw_score": 1.0,
                "confidence": 1.0,
                "weighted_score": 1.0
            })
            contributing_factors.append({
                "source": "sanctions",
                "factor": "Company matches sanctioned entity",
                "severity": "CRITICAL",
                "score_contribution": 1.0
            })

        if sanctions.get("country_hit"):
            severity = sanctions.get("severity", "MEDIUM")
            score_map = {"HIGH": 0.9, "MEDIUM": 0.6, "LOW": 0.3}
            country_score = score_map.get(severity, 0.5)

            weighted_scores.append({
                "source": "specialist_sanctions_country",
                "raw_score": country_score,
                "confidence": 1.0,
                "weighted_score": country_score
            })

            for indicator in sanctions.get("risk_indicators", []):
                contributing_factors.append({
                    "source": "sanctions",
                    "factor": indicator,
                    "severity": severity,
                    "score_contribution": country_score
                })

    if weighted_scores:
        total_weighted = sum(s["weighted_score"] for s in weighted_scores)
        avg_score = total_weighted / len(weighted_scores)
        max_score = max(s["weighted_score"] for s in weighted_scores)
        risk_score = min((avg_score * 0.6) + (max_score * 0.4), 1.0)
    else:
        risk_score = 0.0

    if sanctions.get("company_hit"):
        risk_level = "CRITICAL"
        decision = "BLOCK"
        decision_reason = "Sanctions match detected - automatic block required"
    elif risk_score > RISK_THRESHOLDS["high_risk_score"]:
        risk_level = "HIGH"
        decision = "BLOCK"
        decision_reason = f"Risk score {risk_score:.2f} exceeds high-risk threshold"
    elif risk_score > RISK_THRESHOLDS["medium_risk_score"]:
        risk_level = "MEDIUM"
        decision = "FLAG"
        decision_reason = f"Risk score {risk_score:.2f} requires manual review"
    else:
        risk_level = "LOW"
        decision = "APPROVE"
        decision_reason = f"Risk score {risk_score:.2f} within acceptable limits"

    state["decision"] = {
        "risk_score": round(risk_score, 3),
        "risk_level": risk_level,
        "decision": decision,
        "decision_reason": decision_reason,
        "contributing_factors": contributing_factors,
        "score_breakdown": weighted_scores,
        "signals_processed": len(signals),
        "specialists_consulted": list(specialist_results.keys())
    }

    return state