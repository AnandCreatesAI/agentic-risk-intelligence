# memory/state.py
# Define the State (MOST IMPORTANT)
# Agents communicate only via state - this is the single source of truth.

from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass, field


class RiskState(TypedDict):
    """
    Central state object that flows through the entire workflow.
    All agents read from and write to this state.
    """
    # Input
    input: Dict[str, Any]  # The original declaration/transaction to assess
    
    # Planning
    tasks: List[str]  # Tasks identified by the planner
    
    # Signals from various agents
    signals: List[Dict[str, Any]]  # Risk signals from swarm and specialists
    
    # Specialist results
    specialist_results: Dict[str, Any]  # Results from fact-checking agents
    
    # Final decision
    decision: Dict[str, Any]  # Aggregated risk decision
    
    # Explanation
    explanation: Dict[str, Any]  # Human-readable explanation


# Risk thresholds (configurable)
RISK_THRESHOLDS = {
    "high_value": 1_000_000,  # Transactions above this trigger high-value checks
    "high_risk_score": 0.7,   # Risk scores above this are HIGH risk
    "medium_risk_score": 0.4  # Risk scores above this are MEDIUM risk
}

# Sanctioned countries (example list)
SANCTIONED_COUNTRIES = ["IR", "KP", "SY", "CU", "RU"]

# High-risk industries
HIGH_RISK_INDUSTRIES = ["gambling", "cryptocurrency", "arms", "tobacco"]
