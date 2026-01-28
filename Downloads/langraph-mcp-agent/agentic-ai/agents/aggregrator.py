# agents/aggregator.py
# Aggregator Agent
# Combines all signals from swarm and specialists into a final risk decision.
# This is where THE BUSINESS DECISION is made.

from typing import Dict, Any, List
from memory.state import RISK_THRESHOLDS


def aggregator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregates all risk signals into a final decision.
    
    Combines:
    - Swarm signals (exploratory risk indicators)
    - Specialist results (verified facts)
    - Planner context (initial risk factors)
    
    Produces:
    - Risk score (0.0 to 1.0)
    - Risk level (LOW, MEDIUM, HIGH, CRITICAL)
    - Decision (APPROVE, FLAG, BLOCK)
    - Contributing factors
    
    Args:
        state: Current workflow state with all signals
        
    Returns:
        Updated state with decision
    """
    signals = state.get("signals", [])
    specialist_results = state.get("specialist_results", {})
    risk_factors = state.get("risk_factors", [])
    
    # ========================================
    # Collect all scores with weights
    # ========================================
    weighted_scores = []
    contributing_factors = []
    
    # Process swarm signals
    for signal in signals:
        signal_type = signal.get("type", "unknown")
        score = signal.get("score", 0.0)
        confidence = signal.get("confidence", 0.5)
        
        # Weight by confidence
        weighted_score = score * confidence
        weighted_scores.append({
            "source": f"swarm_{signal_type}",
            "raw_score": score,
            "confidence": confidence,
            "weighted_score": weighted_score
        })
        
        # Add to contributing factors if significant
        if score > 0.3:
            for evidence in signal.get("evidence", []):
                contributing_factors.append({
                    "source": signal_type,
                    "factor": evidence.get("description", evidence.get("type", "Unknown")),
                    "severity": evidence.get("severity", "MEDIUM"),
                    "score_contribution": weighted_score
                })
    
    # ========================================
    # Process specialist results (higher weight)
    # ========================================
    sanctions_result = specialist_results.get("sanctions", {})
    
    if sanctions_result.get("verified"):
        if sanctions_result.get("company_hit"):
            # Company sanctions hit is CRITICAL
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
        
        if sanctions_result.get("country_hit"):
            # Country sanctions hit is HIGH
            severity = sanctions_result.get("severity", "MEDIUM")
            score_map = {"HIGH": 0.9, "MEDIUM": 0.6, "LOW": 0.3}
            country_score = score_map.get(severity, 0.5)
            
            weighted_scores.append({
                "source": "specialist_sanctions_country",
                "raw_score": country_score,
                "confidence": 1.0,
                "weighted_score": country_score
            })
            
            for indicator in sanctions_result.get("risk_indicators", []):
                contributing_factors.append({
                    "source": "sanctions",
                    "factor": indicator,
                    "severity": severity,
                    "score_contribution": country_score
                })
    
    # ========================================
    # Calculate final risk score
    # ========================================
    if weighted_scores:
        # Use weighted average with max boost
        total_weighted = sum(s["weighted_score"] for s in weighted_scores)
        total_weight = len(weighted_scores)
        avg_score = total_weighted / total_weight
        
        # Boost by max score (worst signal matters most)
        max_score = max(s["weighted_score"] for s in weighted_scores)
        
        # Final score: 60% average + 40% max (worst signal carries weight)
        risk_score = min((avg_score * 0.6) + (max_score * 0.4), 1.0)
    else:
        risk_score = 0.0
    
    # ========================================
    # Determine risk level and decision
    # ========================================
    
    # Check for automatic CRITICAL triggers
    has_sanctions_hit = specialist_results.get("sanctions", {}).get("company_hit", False)
    
    if has_sanctions_hit:
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
    
    # ========================================
    # Build final decision object
    # ========================================
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


def get_decision_summary(decision: Dict[str, Any]) -> str:
    """Generate a human-readable decision summary."""
    factors = decision.get("contributing_factors", [])
    
    summary = f"""
Risk Assessment Decision
========================
Risk Score: {decision.get('risk_score', 0):.2%}
Risk Level: {decision.get('risk_level', 'UNKNOWN')}
Decision: {decision.get('decision', 'UNKNOWN')}

Reason: {decision.get('decision_reason', 'N/A')}

Contributing Factors ({len(factors)}):
"""
    for factor in factors[:5]:  # Top 5 factors
        summary += f"  [{factor.get('severity', '?')}] {factor.get('factor', 'Unknown')}\n"
    
    return summary
