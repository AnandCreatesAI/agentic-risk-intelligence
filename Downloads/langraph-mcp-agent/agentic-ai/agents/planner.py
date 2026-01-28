# agents/planner.py
# Planner Agent (Deterministic Brain)
# Decides WHAT needs to be checked based on the input.
# Does NOT make risk decisions - only plans the workflow.

from typing import Dict, Any, List
from memory.state import RISK_THRESHOLDS, SANCTIONED_COUNTRIES, HIGH_RISK_INDUSTRIES


def planner_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic planner that decides which checks are needed.
    
    Business Logic:
    - Country present → sanctions check
    - High value → full swarm analysis
    - Industry present → industry risk check
    
    This prevents unnecessary computation and reduces cost.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with tasks list
    """
    declaration = state["input"]
    tasks = []
    swarm_agents = []
    risk_factors = []
    
    # ========================================
    # Rule 1: Country-based checks
    # ========================================
    country = declaration.get("country", "").upper()
    if country:
        # Always do sanctions check when country is present
        tasks.append("sanctions_check")
        
        # High-risk countries get extra scrutiny
        if country in SANCTIONED_COUNTRIES:
            risk_factors.append(f"Country {country} is on sanctions watchlist")
            swarm_agents.extend(["anomaly", "pattern", "similarity"])
    
    # ========================================
    # Rule 2: Value-based checks
    # ========================================
    value = declaration.get("value", 0)
    
    if value > RISK_THRESHOLDS["high_value"]:
        tasks.append("high_value_review")
        risk_factors.append(f"Value {value:,} exceeds threshold {RISK_THRESHOLDS['high_value']:,}")
        
        # High value transactions get full swarm analysis
        if "anomaly" not in swarm_agents:
            swarm_agents.append("anomaly")
        if "similarity" not in swarm_agents:
            swarm_agents.append("similarity")
        if "pattern" not in swarm_agents:
            swarm_agents.append("pattern")
    
    elif value > RISK_THRESHOLDS["high_value"] * 0.5:
        # Medium value - targeted checks
        tasks.append("medium_value_review")
        if "anomaly" not in swarm_agents:
            swarm_agents.append("anomaly")
    
    # ========================================
    # Rule 3: Industry-based checks
    # ========================================
    industry = declaration.get("industry", "").lower()
    if industry in HIGH_RISK_INDUSTRIES:
        tasks.append("enhanced_due_diligence")
        risk_factors.append(f"Industry '{industry}' is high-risk")
        swarm_agents.extend(["pattern", "similarity"])
    
    # ========================================
    # Rule 4: Company checks
    # ========================================
    company = declaration.get("company", "")
    if company:
        tasks.append("company_verification")
    
    # ========================================
    # Default: At minimum, run basic anomaly detection
    # ========================================
    if not swarm_agents:
        swarm_agents.append("anomaly")
    
    # Remove duplicates while preserving order
    swarm_agents = list(dict.fromkeys(swarm_agents))
    tasks = list(dict.fromkeys(tasks))
    
    # Update state
    state["tasks"] = tasks
    state["swarm_agents"] = swarm_agents
    state["risk_factors"] = risk_factors
    state["signals"] = []  # Initialize signals list
    state["specialist_results"] = {}  # Initialize specialist results
    
    return state


def get_planning_summary(state: Dict[str, Any]) -> str:
    """Generate a human-readable planning summary."""
    tasks = state.get("tasks", [])
    swarm_agents = state.get("swarm_agents", [])
    risk_factors = state.get("risk_factors", [])
    
    summary = f"""
Planning Summary:
================
Tasks Identified: {len(tasks)}
{chr(10).join(f'  - {t}' for t in tasks)}

Swarm Agents to Run: {len(swarm_agents)}
{chr(10).join(f'  - {a}' for a in swarm_agents)}

Initial Risk Factors: {len(risk_factors)}
{chr(10).join(f'  - {r}' for r in risk_factors)}
"""
    return summary
