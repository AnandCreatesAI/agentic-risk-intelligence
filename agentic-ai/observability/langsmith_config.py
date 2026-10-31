import os
from typing import Dict, Any, Optional
from functools import wraps

try:
    from langsmith import Client, traceable
    from langsmith.run_helpers import get_current_run_tree
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False


def setup_langsmith(project_name: str = "agentic-risk-intelligence",
                    api_key: Optional[str] = None) -> bool:
    if not LANGSMITH_AVAILABLE:
        return False

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = project_name

    if api_key:
        os.environ["LANGCHAIN_API_KEY"] = api_key

    return bool(os.environ.get("LANGCHAIN_API_KEY"))


def get_langsmith_client() -> Optional["Client"]:
    if not LANGSMITH_AVAILABLE:
        return None
    try:
        return Client()
    except Exception:
        return None


def trace_agent(agent_name: str, agent_type: str = "agent"):
    def decorator(func):
        if not LANGSMITH_AVAILABLE:
            return func

        @wraps(func)
        @traceable(name=agent_name, run_type=agent_type)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper
    return decorator


def trace_tool(tool_name: str):
    def decorator(func):
        if not LANGSMITH_AVAILABLE:
            return func

        @wraps(func)
        @traceable(name=tool_name, run_type="tool")
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper
    return decorator


def log_risk_decision(
    input_data: Dict[str, Any],
    decision: Dict[str, Any],
    expected_decision: Optional[str] = None,
    feedback_score: Optional[float] = None
):
    if not LANGSMITH_AVAILABLE:
        return

    client = get_langsmith_client()
    if not client:
        return

    try:
        run_tree = get_current_run_tree()
        if not run_tree:
            return

        if feedback_score is not None:
            client.create_feedback(
                run_id=run_tree.id,
                key="accuracy",
                score=feedback_score,
                comment=f"Expected: {expected_decision}, Got: {decision.get('decision')}"
            )

        run_tree.end(outputs={
            "decision": decision,
            "expected": expected_decision,
            "match": decision.get("decision") == expected_decision
            if expected_decision else None
        })
    except Exception:
        pass


def get_project_stats(project_name: str = "agentic-risk-intelligence") -> Dict[str, Any]:
    if not LANGSMITH_AVAILABLE:
        return {"error": "LangSmith not available"}

    client = get_langsmith_client()
    if not client:
        return {"error": "Client unavailable"}

    try:
        runs = list(client.list_runs(project_name=project_name, limit=100))
        if not runs:
            return {"message": "No runs found"}

        total = len(runs)
        success = sum(1 for r in runs if r.status == "success")

        avg_latency = sum(
            (r.end_time - r.start_time).total_seconds()
            for r in runs if r.end_time
        ) / max(total, 1)

        return {
            "total_runs": total,
            "successful_runs": success,
            "error_rate": (total - success) / max(total, 1),
            "avg_latency_seconds": round(avg_latency, 2)
        }
    except Exception as e:
        return {"error": str(e)}