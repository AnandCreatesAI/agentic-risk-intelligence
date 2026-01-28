# agents/explainer.py
# Explanation Agent
# Converts structured risk signals into human-readable explanations.
# Ensures auditability and builds trust with stakeholders.

from typing import Dict, Any, List
from datetime import datetime


def explanation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates human-readable explanation of the risk decision.
    
    This agent creates:
    - Executive summary
    - Detailed evidence trail
    - Confidence assessment
    - Recommended actions
    
    Essential for:
    - Regulatory compliance
    - Audit trails
    - Human review
    - Stakeholder communication
    
    Args:
        state: Current workflow state with decision
        
    Returns:
        Updated state with explanation
    """
    decision = state.get("decision", {})
    signals = state.get("signals", [])
    specialist_results = state.get("specialist_results", {})
    input_data = state.get("input", {})
    
    # ========================================
    # Build Executive Summary
    # ========================================
    risk_level = decision.get("risk_level", "UNKNOWN")
    risk_score = decision.get("risk_score", 0)
    final_decision = decision.get("decision", "UNKNOWN")
    
    executive_summary = _generate_executive_summary(
        input_data, risk_level, risk_score, final_decision, decision.get("decision_reason", "")
    )
    
    # ========================================
    # Build Evidence Trail
    # ========================================
    evidence_trail = _build_evidence_trail(signals, specialist_results)
    
    # ========================================
    # Calculate Confidence
    # ========================================
    confidence_assessment = _assess_confidence(signals, specialist_results)
    
    # ========================================
    # Generate Recommendations
    # ========================================
    recommendations = _generate_recommendations(
        final_decision, risk_level, specialist_results, decision.get("contributing_factors", [])
    )
    
    # ========================================
    # Build Full Explanation
    # ========================================
    state["explanation"] = {
        "timestamp": datetime.now().isoformat(),
        "executive_summary": executive_summary,
        "risk_assessment": {
            "score": risk_score,
            "level": risk_level,
            "decision": final_decision
        },
        "evidence_trail": evidence_trail,
        "confidence": confidence_assessment,
        "recommendations": recommendations,
        "full_narrative": _generate_full_narrative(
            input_data, executive_summary, evidence_trail, 
            confidence_assessment, recommendations
        )
    }
    
    return state


def _generate_executive_summary(
    input_data: Dict, 
    risk_level: str, 
    risk_score: float, 
    decision: str,
    reason: str
) -> str:
    """Generate a concise executive summary."""
    company = input_data.get("company", "Unknown Entity")
    country = input_data.get("country", "Unknown")
    value = input_data.get("value", 0)
    
    decision_text = {
        "APPROVE": "APPROVED for processing",
        "FLAG": "FLAGGED for manual review",
        "BLOCK": "BLOCKED from processing"
    }.get(decision, decision)
    
    return f"""
Transaction involving {company} ({country}) for {value:,.0f} has been assessed.

DECISION: {decision_text}
RISK LEVEL: {risk_level}
RISK SCORE: {risk_score:.1%}

{reason}
""".strip()


def _build_evidence_trail(signals: List[Dict], specialist_results: Dict) -> List[Dict]:
    """Build a chronological evidence trail."""
    evidence = []
    
    # Add swarm evidence
    for signal in signals:
        signal_type = signal.get("type", "unknown")
        for item in signal.get("evidence", []):
            evidence.append({
                "source": f"Swarm Analysis ({signal_type})",
                "type": item.get("type", "observation"),
                "finding": item.get("description", str(item)),
                "severity": item.get("severity", "INFO"),
                "score_impact": signal.get("score", 0)
            })
    
    # Add specialist evidence
    sanctions = specialist_results.get("sanctions", {})
    if sanctions.get("verified"):
        for item in sanctions.get("evidence", []):
            evidence.append({
                "source": "Sanctions Verification",
                "type": item.get("type", "verification"),
                "finding": f"{item.get('type', 'Hit')}: {item.get('entity', item.get('country', 'Unknown'))}",
                "severity": item.get("severity", "HIGH"),
                "source_authority": item.get("source", "Unknown")
            })
    
    return evidence


def _assess_confidence(signals: List[Dict], specialist_results: Dict) -> Dict:
    """Assess overall confidence in the decision."""
    confidences = []
    
    # Collect signal confidences
    for signal in signals:
        confidences.append(signal.get("confidence", 0.5))
    
    # Specialist results have high confidence
    if specialist_results.get("sanctions", {}).get("verified"):
        confidences.append(0.95)  # Sanctions checks are highly reliable
    
    if not confidences:
        avg_confidence = 0.5
    else:
        avg_confidence = sum(confidences) / len(confidences)
    
    # Determine confidence level
    if avg_confidence >= 0.8:
        level = "HIGH"
        description = "Decision supported by strong, verified evidence"
    elif avg_confidence >= 0.6:
        level = "MEDIUM"
        description = "Decision based on moderate evidence; additional review may be warranted"
    else:
        level = "LOW"
        description = "Limited evidence available; manual review recommended"
    
    return {
        "level": level,
        "score": round(avg_confidence, 2),
        "description": description,
        "factors_analyzed": len(confidences)
    }


def _generate_recommendations(
    decision: str, 
    risk_level: str, 
    specialist_results: Dict,
    contributing_factors: List[Dict]
) -> List[str]:
    """Generate actionable recommendations."""
    recommendations = []
    
    if decision == "BLOCK":
        recommendations.append("Do not proceed with this transaction")
        
        if specialist_results.get("sanctions", {}).get("hit"):
            recommendations.append("Report to compliance team immediately")
            recommendations.append("Document all related parties for SAR filing")
        
        recommendations.append("Retain all documentation for audit purposes")
    
    elif decision == "FLAG":
        recommendations.append("Escalate to senior compliance officer for review")
        recommendations.append("Request additional documentation from counterparty")
        recommendations.append("Verify company registration and beneficial ownership")
        
        # Specific recommendations based on factors
        for factor in contributing_factors:
            if "country" in factor.get("factor", "").lower():
                recommendations.append("Verify legitimate business purpose for country exposure")
            if "value" in factor.get("factor", "").lower():
                recommendations.append("Confirm source of funds documentation")
    
    else:  # APPROVE
        recommendations.append("Proceed with standard processing")
        if risk_level == "MEDIUM":
            recommendations.append("Consider enhanced monitoring for this relationship")
    
    return list(dict.fromkeys(recommendations))  # Remove duplicates


def _generate_full_narrative(
    input_data: Dict,
    summary: str,
    evidence: List[Dict],
    confidence: Dict,
    recommendations: List[str]
) -> str:
    """Generate a complete narrative explanation."""
    company = input_data.get("company", "Unknown")
    country = input_data.get("country", "Unknown")
    value = input_data.get("value", 0)
    
    narrative = f"""
RISK ASSESSMENT REPORT
======================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUBJECT
-------
Entity: {company}
Jurisdiction: {country}
Transaction Value: {value:,.0f}

SUMMARY
-------
{summary}

EVIDENCE ANALYSIS
-----------------
"""
    
    if evidence:
        for i, item in enumerate(evidence, 1):
            narrative += f"""
{i}. [{item.get('severity', 'INFO')}] {item.get('source', 'Unknown')}
   Finding: {item.get('finding', 'N/A')}
"""
    else:
        narrative += "No significant risk indicators identified.\n"
    
    narrative += f"""
CONFIDENCE ASSESSMENT
---------------------
Confidence Level: {confidence.get('level', 'UNKNOWN')}
Confidence Score: {confidence.get('score', 0):.0%}
Assessment: {confidence.get('description', 'N/A')}

RECOMMENDATIONS
---------------
"""
    
    for i, rec in enumerate(recommendations, 1):
        narrative += f"{i}. {rec}\n"
    
    narrative += """
---
This report was generated by the Agentic Risk Intelligence System.
All findings are based on available data at the time of assessment.
"""
    
    return narrative.strip()


def get_explanation_summary(explanation: Dict[str, Any]) -> str:
    """Get a brief summary of the explanation."""
    return explanation.get("executive_summary", "No summary available")
