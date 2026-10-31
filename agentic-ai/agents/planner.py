from typing import Dict, Any, List
from memory.state import RISK_THRESHOLDS, SANCTIONED_COUNTRIES, HIGH_RISK_INDUSTRIES


def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    declaration = state["input"]

    tasks: List[str] = []
    swarm_agents: List[str] = []
    risk_factors: List[str] = []

    country = str(declaration.get("country", "")).upper()
    value = float(declaration.get("value", 0) or 0)
    industry = str(declaration.get("industry", "")).lower()
    company = declaration.get("company")

    if country:
        tasks.append("sanctions_check")
        if country in SANCTIONED_COUNTRIES:
            risk_factors.append(f"Country {country} is on sanctions watchlist")
            swarm_agents.extend(["anomaly", "pattern", "similarity"])

    high_value_threshold = RISK_THRESHOLDS["high_value"]

    if value > high_value_threshold:
        tasks.append("high_value_review")
        risk_factors.append(
            f"Value {value:,.0f} exceeds threshold {high_value_threshold:,.0f}"
        )
        swarm_agents.extend(["anomaly", "similarity", "pattern"])

    elif value > high_value_threshold * 0.5:
        tasks.append("medium_value_review")
        swarm_agents.append("anomaly")

    if industry and industry in HIGH_RISK_INDUSTRIES:
        tasks.append("enhanced_due_diligence")
        risk_factors.append(f"Industry '{industry}' is high-risk")
        swarm_agents.extend(["pattern", "similarity"])

    if company:
        tasks.append("company_verification")

    if not swarm_agents:
        swarm_agents = ["anomaly"]

    state["tasks"] = list(dict.fromkeys(tasks))
    state["swarm_agents"] = list(dict.fromkeys(swarm_agents))
    state["risk_factors"] = risk_factors
    state["signals"] = []
    state["specialist_results"] = {}

    return state