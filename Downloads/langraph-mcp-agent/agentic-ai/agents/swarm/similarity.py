# agents/swarm/similarity.py
# Similarity Detection Swarm Agent
# Finds similar historical cases that may indicate risk.
# Produces SIGNALS, not decisions.

from typing import Dict, Any, List
from a2a.messages import task, signal
from a2a.dispatcher import dispatch


def similarity_agent(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Swarm agent that finds similar historical risky cases.
    
    This agent is:
    - Fast: Runs in parallel with other swarm agents
    - Isolated: Only accesses tools via MCP
    - Signal-only: Produces risk signals, doesn't make decisions
    
    Args:
        data: Transaction/declaration data to analyze
        
    Returns:
        Signal dictionary with similarity findings
    """
    # Create task message for A2A dispatch
    msg = task(
        sender="swarm_similarity",
        receiver="similarity_searcher",
        name="similarity_search",
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
            "type": "similarity",
            "score": 0.0,
            "confidence": 0.0,
            "evidence": [],
            "error": response["error"]
        }
    
    result_data = response["content"]["data"]
    matches = result_data.get("matches", [])
    highest_similarity = result_data.get("highest_similarity", 0.0)
    
    # Build evidence from similar cases
    evidence = []
    for match in matches[:3]:  # Top 3 matches
        case = match["case"]
        evidence.append({
            "type": "similar_case",
            "similarity_score": match["similarity"],
            "historical_company": case["company"],
            "historical_country": case["country"],
            "historical_outcome": case["outcome"],
            "historical_risk_score": case["risk_score"]
        })
    
    # Score based on highest similarity and outcome severity
    score = 0.0
    if matches:
        # Weight by similarity and historical risk
        for match in matches:
            case = match["case"]
            weight = match["similarity"] * case["risk_score"]
            score = max(score, weight)
    
    # Confidence based on match quality
    confidence = min(0.6 + (highest_similarity * 0.3), 0.9) if matches else 0.3
    
    return {
        "type": "similarity",
        "score": round(score, 2),
        "confidence": confidence,
        "similar_cases_found": len(matches),
        "highest_similarity": highest_similarity,
        "evidence": evidence,
        "raw_response": result_data
    }
