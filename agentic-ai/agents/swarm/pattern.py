from typing import Dict, Any
from a2a.messages import task
from a2a.dispatcher import dispatch


def pattern_agent(data: Dict[str, Any]) -> Dict[str, Any]:
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

    response = dispatch(msg)

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

    severity_weights = {"HIGH": 1.0, "MEDIUM": 0.6, "LOW": 0.3}

    evidence = [
        {
            "type": p.get("type"),
            "description": p.get("description"),
            "severity": p.get("severity"),
            "weight": severity_weights.get(p.get("severity"), 0.5)
        }
        for p in patterns
    ]

    high_count = sum(1 for p in patterns if p.get("severity") == "HIGH")
    confidence = (
        min(0.7 + (high_count * 0.1), 0.95)
        if patterns else 0.5
    )

    return {
        "type": "pattern",
        "score": pattern_score,
        "confidence": confidence,
        "patterns_found": len(patterns),
        "evidence": evidence,
        "raw_response": result_data
    }