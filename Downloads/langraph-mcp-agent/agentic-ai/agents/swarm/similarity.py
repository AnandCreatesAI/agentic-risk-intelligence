from typing import Dict, Any
from a2a.messages import task
from a2a.dispatcher import dispatch


def similarity_agent(data: Dict[str, Any]) -> Dict[str, Any]:
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

    response = dispatch(msg)

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

    evidence = []
    score = 0.0

    for match in matches[:3]:
        case = match.get("case", {})
        similarity = match.get("similarity", 0.0)

        evidence.append({
            "type": "similar_case",
            "similarity_score": similarity,
            "historical_company": case.get("company"),
            "historical_country": case.get("country"),
            "historical_outcome": case.get("outcome"),
            "historical_risk_score": case.get("risk_score")
        })

        weighted = similarity * case.get("risk_score", 0.0)
        score = max(score, weighted)

    confidence = (
        min(0.6 + (highest_similarity * 0.3), 0.9)
        if matches else 0.3
    )

    return {
        "type": "similarity",
        "score": round(score, 2),
        "confidence": confidence,
        "similar_cases_found": len(matches),
        "highest_similarity": highest_similarity,
        "evidence": evidence,
        "raw_response": result_data
    }