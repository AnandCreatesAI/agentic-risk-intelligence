# agents/swarm/anomaly.py
# Anomaly Detection Swarm Agent
# Detects statistical anomalies and unusual patterns in transactions.
# Produces SIGNALS, not decisions.

from typing import Dict, Any, List
from a2a.messages import task, signal
from a2a.dispatcher import dispatch


def anomaly_agent(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Swarm agent that detects anomalies in transaction data.
    
    This agent is:
    - Fast: Runs in parallel with other swarm agents
    - Isolated: Only accesses tools via MCP
    - Signal-only: Produces risk signals, doesn't make decisions
    
    Args:
        data: Transaction/declaration data to analyze
        
    Returns:
        Signal dictionary with anomaly findings
    """
    # Create task message for A2A dispatch
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
    
    # Dispatch through A2A layer
    response = dispatch(msg)
    
    # Extract results
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
    
    # Build evidence list
    evidence = []
    for anomaly in anomalies:
        evidence.append({
            "type": anomaly["type"],
            "description": anomaly["description"],
            "severity": anomaly["severity"]
        })
    
    # Calculate confidence based on number of anomalies detected
    confidence = min(0.5 + (len(anomalies) * 0.15), 0.95)
    
    return {
        "type": "anomaly",
        "score": anomaly_score,
        "confidence": confidence,
        "is_anomalous": result_data.get("is_anomalous", False),
        "evidence": evidence,
        "raw_response": result_data
    }
