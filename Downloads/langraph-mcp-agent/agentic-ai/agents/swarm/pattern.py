# agents/swarm/pattern.py
# Pattern Detection Swarm Agent
# Identifies known risky patterns (structuring, layering, threshold evasion).
# Produces SIGNALS, not decisions.

from typing import Dict, Any, List
from a2a.messages import task, signal
from a2a.dispatcher import dispatch


def pattern_agent(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Swarm agent that detects known risky transaction patterns.
    
    This agent is:
    - Fast: Runs in parallel with other swarm agents
    - Isolated: Only accesses tools via MCP
    - Signal-only: Produces risk signals, doesn't make decisions
    
    Patterns detected:
    - Structuring (breaking up transactions)
    - Threshold proximity (just under limits)
    - High-risk corridors
    - Round number transactions
    
    Args:
        data: Transaction/declaration data to analyze
        
    Returns:
        Signal dictionary with pattern findings
    """
    # Create task message for A2A dispatch
    msg = task(
        sender="swarm_pattern",
        receiver="pattern_detector",
        name="pattern_check",
        payload={
            "company": data.get("company", ""),
            "country": data.get("country", ""),
            "value": data.get("value", 0)
        }
    )
    
    # Dispatch through A2A layer
    response = dispatch(msg)
    
    # Extract results
    if "error" in response:
        return {
            "type": "pattern",
            "score": 0.0,
            "confidence": 0.0,
            "evidence": [],
            "error": response["error"]
        }
    
    result_data = response["content"]["data"]
    patterns = result_data.get("patterns", [])
    pattern_score = result_data.get("pattern_score", 0.0)
    
    # Build evidence from patterns found
    evidence = []
    severity_weights = {"HIGH": 1.0, "MEDIUM": 0.6, "LOW": 0.3}
    
    for pattern in patterns:
        evidence.append({
            "type": pattern["type"],
            "description": pattern["description"],
            "severity": pattern["severity"],
            "weight": severity_weights.get(pattern["severity"], 0.5)
        })
    
    # Confidence based on pattern detection quality
    high_severity_count = sum(1 for p in patterns if p["severity"] == "HIGH")
    confidence = min(0.7 + (high_severity_count * 0.1), 0.95) if patterns else 0.5
    
    return {
        "type": "pattern",
        "score": pattern_score,
        "confidence": confidence,
        "patterns_found": len(patterns),
        "evidence": evidence,
        "raw_response": result_data
    }
