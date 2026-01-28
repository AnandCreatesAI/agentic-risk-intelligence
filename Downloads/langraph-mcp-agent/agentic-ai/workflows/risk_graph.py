# workflows/risk_graph.py
# LangGraph Workflow for Risk Assessment
# Orchestrates the complete flow: Plan → Swarm → Specialists → Aggregate → Explain

from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from memory.state import RiskState
from agents.planner import planner_node
from agents.aggregrator import aggregator_node
#from agents.explainer import explanation_node
from agents.explainer_llm import explanation_node_llm as explanation_node
from agents.swarm.run import run_swarm
from agents.specialists.sanctions import run_specialists


# ============================================================================
# WORKFLOW NODES
# ============================================================================

def swarm_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute swarm agents in parallel.
    Swarm agents explore and produce risk signals.
    """
    declaration = state["input"]
    swarm_agents = state.get("swarm_agents", ["anomaly"])
    
    # Run swarm and collect signals
    signals = run_swarm(declaration, agents=swarm_agents)
    
    # Add signals to state
    state["signals"] = signals
    
    return state


def specialist_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute specialist agents for fact verification.
    Specialists check against authoritative sources.
    """
    declaration = state["input"]
    tasks = state.get("tasks", [])
    
    # Run specialists based on planner tasks
    results = run_specialists(declaration, tasks)
    
    # Add results to state
    state["specialist_results"] = results
    
    return state


# ============================================================================
# CONDITIONAL ROUTING
# ============================================================================

def should_run_specialists(state: Dict[str, Any]) -> str:
    """
    Determine if specialist checks are needed.
    Based on tasks identified by planner.
    """
    tasks = state.get("tasks", [])
    
    # Check if any task requires specialist verification
    specialist_tasks = ["sanctions_check", "pep_check", "adverse_media", "company_verification"]
    
    if any(task in specialist_tasks for task in tasks):
        return "specialists"
    
    return "aggregate"


def should_run_swarm(state: Dict[str, Any]) -> str:
    """
    Determine if swarm analysis is needed.
    Based on swarm_agents identified by planner.
    """
    swarm_agents = state.get("swarm_agents", [])
    
    if swarm_agents:
        return "swarm"
    
    return "aggregate"

# Removed explanation_router - was causing infinite loop

# ============================================================================
# BUILD THE WORKFLOW GRAPH
# ============================================================================

def build_risk_workflow() -> StateGraph:
    """
    Build the complete risk assessment workflow.
    
    Flow:
    1. Planner → Decides what checks are needed
    2. Swarm → Parallel exploration for risk signals (if needed)
    3. Specialists → Fact verification (if needed)
    4. Aggregator → Combines all signals into decision
    5. Explainer → Creates human-readable explanation
    
    Returns:
        Compiled LangGraph workflow
    """
    # Create the graph with our state type
    graph = StateGraph(RiskState)
    
    # Add all nodes
    graph.add_node("plan", planner_node)
    graph.add_node("swarm", swarm_node)
    graph.add_node("specialists", specialist_node)
    graph.add_node("aggregate", aggregator_node)
    graph.add_node("explain", explanation_node)
    
    # Set entry point
    graph.set_entry_point("plan")
    
    # Add edges with conditional routing
    # After planning, run swarm (most cases need exploration)
    graph.add_edge("plan", "swarm")
    
    # After swarm, check if specialists are needed
    graph.add_conditional_edges(
        "swarm",
        should_run_specialists,
        {
            "specialists": "specialists",
            "aggregate": "aggregate"
        }
    )
    
    # After specialists, aggregate
    graph.add_edge("specialists", "aggregate")
    
    # After aggregation, explain
    graph.add_edge("aggregate", "explain")
    
    # End after explanation
    graph.add_edge("explain", END)
    
    return graph


def build_simple_workflow() -> StateGraph:
    """
    Build a simplified linear workflow (for testing/debugging).
    
    Flow: Plan → Swarm → Specialists → Aggregate → Explain
    """
    graph = StateGraph(RiskState)
    
    graph.add_node("plan", planner_node)
    graph.add_node("swarm", swarm_node)
    graph.add_node("specialists", specialist_node)
    graph.add_node("aggregate", aggregator_node)
    graph.add_node("explain", explanation_node)
    
    graph.set_entry_point("plan")
    graph.add_edge("plan", "swarm")
    graph.add_edge("swarm", "specialists")
    graph.add_edge("specialists", "aggregate")
    graph.add_edge("aggregate", "explain")
    graph.add_edge("explain", END)
    
    return graph


# ============================================================================
# COMPILED WORKFLOWS
# ============================================================================

# Main workflow with conditional routing
workflow = build_risk_workflow().compile()

# Simple linear workflow (for debugging)
simple_workflow = build_simple_workflow().compile()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def run_assessment(declaration: Dict[str, Any], simple: bool = False) -> Dict[str, Any]:
    """
    Run a complete risk assessment on a declaration.
    
    Args:
        declaration: The input data to assess
        simple: Use simple linear workflow instead of conditional
        
    Returns:
        Complete workflow result
    """
    initial_state = {
        "input": declaration,
        "tasks": [],
        "swarm_agents": [],
        "risk_factors": [],
        "signals": [],
        "specialist_results": {},
        "decision": {},
        "explanation": {}
    }
    
    wf = simple_workflow if simple else workflow
    return wf.invoke(initial_state)


def get_decision(result: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the decision from workflow result."""
    return result.get("decision", {})


def get_explanation(result: Dict[str, Any]) -> str:
    """Extract the full narrative explanation from workflow result."""
    return result.get("explanation", {}).get("full_narrative", "No explanation available")
