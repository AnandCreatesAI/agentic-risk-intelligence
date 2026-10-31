from typing import Dict, Any
from langgraph.graph import StateGraph, END
from memory.state import RiskState
from agents.planner import planner_node
from agents.aggregator import aggregator_node
from agents.explainer_llm import explanation_node_llm as explanation_node
from agents.swarm.run import run_swarm
from agents.specialists.sanctions import run_specialists


def swarm_node(state: RiskState) -> RiskState:
    declaration = state["input"]
    swarm_agents = state.get("swarm_agents") or ["anomaly"]
    signals = run_swarm(declaration, agents=swarm_agents)
    state["signals"] = signals
    return state


def specialist_node(state: RiskState) -> RiskState:
    declaration = state["input"]
    tasks = state.get("tasks") or []
    results = run_specialists(declaration, tasks)
    state["specialist_results"] = results
    return state


def should_run_specialists(state: RiskState) -> str:
    tasks = state.get("tasks") or []
    specialist_tasks = {
        "sanctions_check",
        "pep_check",
        "adverse_media",
        "company_verification"
    }
    return "specialists" if any(t in specialist_tasks for t in tasks) else "aggregate"


def build_risk_workflow() -> StateGraph:
    graph = StateGraph(RiskState)

    graph.add_node("plan", planner_node)
    graph.add_node("swarm", swarm_node)
    graph.add_node("specialists", specialist_node)
    graph.add_node("aggregate", aggregator_node)
    graph.add_node("explain", explanation_node)

    graph.set_entry_point("plan")

    graph.add_edge("plan", "swarm")

    graph.add_conditional_edges(
        "swarm",
        should_run_specialists,
        {
            "specialists": "specialists",
            "aggregate": "aggregate"
        }
    )

    graph.add_edge("specialists", "aggregate")
    graph.add_edge("aggregate", "explain")
    graph.add_edge("explain", END)

    return graph


workflow = build_risk_workflow().compile()


def run_assessment(declaration: Dict[str, Any]) -> RiskState:
    initial_state: RiskState = {
        "input": declaration,
        "tasks": [],
        "swarm_agents": [],
        "risk_factors": [],
        "signals": [],
        "specialist_results": {},
        "decision": {},
        "explanation": {}
    }
    return workflow.invoke(initial_state)


def get_decision(state: RiskState) -> Dict[str, Any]:
    return state.get("decision", {})


def get_explanation(state: RiskState) -> str:
    explanation = state.get("explanation", {})
    return explanation.get("full_narrative", "No explanation available.")