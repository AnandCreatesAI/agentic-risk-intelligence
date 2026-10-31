from typing import Dict, Any
from a2a.messages import task
from a2a.dispatcher import dispatch


def sanctions_agent(declaration: Dict[str, Any]) -> Dict[str, Any]:
    msg = task(
        sender="planner",
        receiver="sanctions_agent",
        name="sanctions_check",
        payload={
            "company": declaration.get("company", ""),
            "country": declaration.get("country")
        }
    )

    response = dispatch(msg)

    if "error" in response:
        return {
            "agent": "sanctions",
            "verified": False,
            "hit": False,
            "error": response["error"],
            "evidence": []
        }

    result_data = response["content"]["data"]

    evidence = []

    if result_data.get("company_hit"):
        for source in result_data.get("sources", []):
            if source.get("type") == "company_sanction":
                evidence.append({
                    "type": "company_sanctions_hit",
                    "entity": source.get("name"),
                    "source": source.get("source"),
                    "date_listed": source.get("date"),
                    "severity": "CRITICAL"
                })

    if result_data.get("country_hit"):
        for source in result_data.get("sources", []):
            if source.get("type") == "country_sanction":
                severity = "HIGH" if source.get("level") == "comprehensive" else "MEDIUM"
                evidence.append({
                    "type": "country_sanctions_hit",
                    "country": source.get("country"),
                    "sanction_level": source.get("level"),
                    "source": source.get("source"),
                    "severity": severity
                })

    return {
        "agent": "sanctions",
        "verified": True,
        "hit": result_data.get("hit", False),
        "company_hit": result_data.get("company_hit", False),
        "country_hit": result_data.get("country_hit", False),
        "severity": result_data.get("severity", "NONE"),
        "risk_indicators": result_data.get("risk_indicators", []),
        "evidence": evidence,
        "timestamp": result_data.get("timestamp"),
        "raw_response": result_data
    }


def run_specialists(declaration: Dict[str, Any], tasks: list) -> Dict[str, Any]:
    results = {}

    for task_name in tasks:
        if task_name == "sanctions_check":
            results["sanctions"] = sanctions_agent(declaration)

    return results