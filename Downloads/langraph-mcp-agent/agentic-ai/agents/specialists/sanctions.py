# agents/specialists/sanctions.py
# Sanctions Specialist Agent
# Performs fact-based verification against official sanctions lists.
# Produces VERIFIED FACTS, not opinions.

from typing import Dict, Any
from a2a.messages import task
from a2a.dispatcher import dispatch


def sanctions_agent(declaration: Dict[str, Any]) -> Dict[str, Any]:
    """
    Specialist agent that performs sanctions verification.
    
    This agent is:
    - Fact-based: Checks against official lists (OFAC, EU, UN)
    - Deterministic: Same input always produces same output
    - Auditable: All checks are logged with sources
    
    Args:
        declaration: The transaction/entity to verify
        
    Returns:
        Verification result with evidence
    """
    # Create A2A task message
    msg = task(
        sender="planner",
        receiver="sanctions_agent",
        name="sanctions_check",
        payload={
            "company": declaration.get("company", ""),
            "country": declaration.get("country")
        }
    )
    
    # Dispatch through A2A layer (which calls MCP tools)
    response = dispatch(msg)
    
    # Handle errors
    if "error" in response:
        return {
            "agent": "sanctions",
            "verified": False,
            "hit": False,
            "error": response["error"],
            "evidence": []
        }
    
    # Extract result data
    result_data = response["content"]["data"]
    
    # Build structured verification result
    evidence = []
    
    # Add company hit evidence
    if result_data.get("company_hit"):
        for source in result_data.get("sources", []):
            if source["type"] == "company_sanction":
                evidence.append({
                    "type": "company_sanctions_hit",
                    "entity": source["name"],
                    "source": source["source"],
                    "date_listed": source["date"],
                    "severity": "CRITICAL"
                })
    
    # Add country hit evidence
    if result_data.get("country_hit"):
        for source in result_data.get("sources", []):
            if source["type"] == "country_sanction":
                evidence.append({
                    "type": "country_sanctions_hit",
                    "country": source["country"],
                    "sanction_level": source["level"],
                    "source": source["source"],
                    "severity": "HIGH" if source["level"] == "comprehensive" else "MEDIUM"
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
    """
    Run all required specialist agents based on planner tasks.
    
    Args:
        declaration: The input data
        tasks: List of tasks from the planner
        
    Returns:
        Dictionary of specialist results
    """
    results = {}
    
    for task_name in tasks:
        if task_name == "sanctions_check":
            results["sanctions"] = sanctions_agent(declaration)
        # Add more specialists here as needed
        # elif task_name == "pep_check":
        #     results["pep"] = pep_agent(declaration)
        # elif task_name == "adverse_media":
        #     results["adverse_media"] = adverse_media_agent(declaration)
    
    return results
