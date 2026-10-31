from typing import Dict, Any
from a2a.messages import task
from a2a.dispatcher import dispatch


def anomaly_agent(data: Dict[str, Any]) -> Dict[str, Any]:
    msg = task(
        sender="swarm_anomaly",
        receiver="anomaly_detector",
        name="anomaly_detection",
        payload={
            "company": data.get("company", ""),
            "country": data.get("country", ""),
            "value": data.get("value", 0)
        }
    )

    response = dispatch(msg)

    if "error" in response:
        return {
            "type": "anomaly",
            "score": 0.0,
            "confidence": 0.0,
            "evidence": [],
            "error": response["error"]
        }

    result_data = response["content"]["data"]
    anomalies = result_data.get("anomalies", [])
    anomaly_score = result_data.get("anomaly_score", 0.0)

    evidence = [
        {
            "type": anomaly.get("type"),
            "description": anomaly.get("description"),
            "severity": anomaly.get("severity")
        }
        for anomaly in anomalies
    ]

    confidence = min(0.5 + (len(anomalies) * 0.15), 0.95)

    return {
        "type": "anomaly",
        "score": anomaly_score,
        "confidence": confidence,
        "is_anomalous": result_data.get("is_anomalous", False),
        "evidence": evidence,
        "raw_response": result_data
    }