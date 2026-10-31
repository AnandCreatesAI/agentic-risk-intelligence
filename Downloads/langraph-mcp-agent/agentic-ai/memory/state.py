from typing import TypedDict, List, Dict, Any


class RiskState(TypedDict, total=False):
    input: Dict[str, Any]

    tasks: List[str]
    swarm_agents: List[str]
    risk_factors: List[str]

    signals: List[Dict[str, Any]]
    specialist_results: Dict[str, Any]

    decision: Dict[str, Any]
    explanation: Dict[str, Any]


RISK_THRESHOLDS = {
    "high_value": 1_000_000,
    "high_risk_score": 0.7,
    "medium_risk_score": 0.4
}

SANCTIONED_COUNTRIES = ["IR", "KP", "SY", "CU", "RU"]

HIGH_RISK_INDUSTRIES = ["gambling", "cryptocurrency", "arms", "tobacco"]