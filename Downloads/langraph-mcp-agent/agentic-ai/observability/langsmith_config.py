# observability/langsmith_config.py
# LangSmith Integration for Observability
# Provides tracing, debugging, and monitoring for the risk assessment workflow.

import os
from typing import Dict, Any, Optional
from functools import wraps
import logging

logger = logging.getLogger("LangSmith")

# Check if LangSmith is available
try:
    from langsmith import Client, traceable
    from langsmith.run_helpers import get_current_run_tree
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    logger.warning("LangSmith not installed. Run: pip install langsmith")


def setup_langsmith(
    project_name: str = "agentic-risk-intelligence",
    api_key: Optional[str] = None
) -> bool:
    """
    Configure LangSmith for tracing.
    
    Args:
        project_name: Name of the project in LangSmith dashboard
        api_key: LangSmith API key (or set LANGCHAIN_API_KEY env var)
        
    Returns:
        True if setup successful, False otherwise
    """
    if not LANGSMITH_AVAILABLE:
        logger.warning("LangSmith not available")
        return False
    
    # Set environment variables for LangChain/LangGraph auto-tracing
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = project_name
    
    if api_key:
        os.environ["LANGCHAIN_API_KEY"] = api_key
    
    # Verify configuration
    if not os.environ.get("LANGCHAIN_API_KEY"):
        logger.warning("LANGCHAIN_API_KEY not set. Tracing disabled.")
        return False
    
    logger.info(f"LangSmith configured for project: {project_name}")
    return True


def get_langsmith_client() -> Optional["Client"]:
    """Get LangSmith client for programmatic access."""
    if not LANGSMITH_AVAILABLE:
        return None
    
    try:
        return Client()
    except Exception as e:
        logger.error(f"Failed to create LangSmith client: {e}")
        return None


# ============================================================================
# CUSTOM TRACING DECORATORS
# ============================================================================

def trace_agent(agent_name: str, agent_type: str = "agent"):
    """
    Decorator to trace agent execution with custom metadata.
    
    Usage:
        @trace_agent("anomaly_agent", "swarm")
        def anomaly_agent(data):
            ...
    """
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
    """
    Decorator to trace MCP tool execution.
    
    Usage:
        @trace_tool("check_sanctions")
        def check_sanctions(company, country):
            ...
    """
    def decorator(func):
        if not LANGSMITH_AVAILABLE:
            return func
        
        @wraps(func)
        @traceable(name=tool_name, run_type="tool")
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# ============================================================================
# EVALUATION HELPERS
# ============================================================================

def log_risk_decision(
    input_data: Dict[str, Any],
    decision: Dict[str, Any],
    expected_decision: Optional[str] = None,
    feedback_score: Optional[float] = None
):
    """
    Log a risk decision for evaluation and feedback.
    
    This enables:
    - Building evaluation datasets
    - A/B testing different risk models
    - Tracking decision accuracy over time
    
    Args:
        input_data: The original declaration/transaction
        decision: The system's decision
        expected_decision: Ground truth (for labeled data)
        feedback_score: Human feedback score (0-1)
    """
    if not LANGSMITH_AVAILABLE:
        return
    
    client = get_langsmith_client()
    if not client:
        return
    
    try:
        # Get current run if in a traced context
        run_tree = get_current_run_tree()
        if run_tree:
            # Add feedback to the run
            if feedback_score is not None:
                client.create_feedback(
                    run_id=run_tree.id,
                    key="accuracy",
                    score=feedback_score,
                    comment=f"Expected: {expected_decision}, Got: {decision.get('decision')}"
                )
            
            # Add outputs for evaluation
            run_tree.end(outputs={
                "decision": decision,
                "expected": expected_decision,
                "match": decision.get("decision") == expected_decision if expected_decision else None
            })
    except Exception as e:
        logger.error(f"Failed to log decision: {e}")


def create_evaluation_dataset(
    dataset_name: str,
    examples: list
) -> Optional[str]:
    """
    Create a dataset in LangSmith for evaluating risk decisions.
    
    Args:
        dataset_name: Name for the dataset
        examples: List of {"input": {...}, "expected_output": {...}} dicts
        
    Returns:
        Dataset ID if successful
    """
    if not LANGSMITH_AVAILABLE:
        return None
    
    client = get_langsmith_client()
    if not client:
        return None
    
    try:
        # Create dataset
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description="Risk assessment evaluation dataset"
        )
        
        # Add examples
        for example in examples:
            client.create_example(
                inputs=example["input"],
                outputs=example.get("expected_output", {}),
                dataset_id=dataset.id
            )
        
        logger.info(f"Created dataset '{dataset_name}' with {len(examples)} examples")
        return dataset.id
        
    except Exception as e:
        logger.error(f"Failed to create dataset: {e}")
        return None


# ============================================================================
# MONITORING HELPERS
# ============================================================================

def get_project_stats(project_name: str = "agentic-risk-intelligence") -> Dict[str, Any]:
    """
    Get statistics for the project from LangSmith.
    
    Returns metrics like:
    - Total runs
    - Average latency
    - Error rate
    - Decision distribution
    """
    if not LANGSMITH_AVAILABLE:
        return {"error": "LangSmith not available"}
    
    client = get_langsmith_client()
    if not client:
        return {"error": "Could not connect to LangSmith"}
    
    try:
        # Get recent runs
        runs = list(client.list_runs(
            project_name=project_name,
            limit=100
        ))
        
        if not runs:
            return {"message": "No runs found"}
        
        # Calculate stats
        total_runs = len(runs)
        successful_runs = sum(1 for r in runs if r.status == "success")
        avg_latency = sum(
            (r.end_time - r.start_time).total_seconds() 
            for r in runs if r.end_time
        ) / max(total_runs, 1)
        
        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "error_rate": (total_runs - successful_runs) / max(total_runs, 1),
            "avg_latency_seconds": round(avg_latency, 2)
        }
        
    except Exception as e:
        return {"error": str(e)}
