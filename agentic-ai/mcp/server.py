from typing import Dict, Any, Callable
from datetime import datetime
import logging

from mcp.tools import (
    check_sanctions,
    search_similar_cases,
    detect_anomalies,
    check_patterns,
    get_company_info
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCP")

TOOLS: Dict[str, Callable] = {
    "check_sanctions": check_sanctions,
    "search_similar_cases": search_similar_cases,
    "detect_anomalies": detect_anomalies,
    "check_patterns": check_patterns,
    "get_company_info": get_company_info,
}

TOOL_METADATA = {
    "check_sanctions": {"requires_audit": True},
    "search_similar_cases": {"requires_audit": False},
    "detect_anomalies": {"requires_audit": False},
    "check_patterns": {"requires_audit": False},
    "get_company_info": {"requires_audit": True},
}

_audit_log = []


def _summarize_result(result: Any) -> str:
    if isinstance(result, dict):
        if "hit" in result:
            return f"hit={result['hit']}"
        if "anomaly_score" in result:
            return f"anomaly_score={result['anomaly_score']}"
        if "pattern_score" in result:
            return f"pattern_score={result['pattern_score']}"
    return "completed"


def _log_tool_call(tool_name: str, kwargs: Dict, result: Any, caller: str):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "caller": caller,
        "inputs": kwargs,
        "result_summary": _summarize_result(result),
        "requires_audit": TOOL_METADATA.get(tool_name, {}).get("requires_audit", False)
    }
    _audit_log.append(entry)
    logger.info(f"Tool called: {tool_name} by {caller}")


def call_tool(name: str, caller: str = "unknown", **kwargs) -> Dict[str, Any]:
    if name not in TOOLS:
        return {
            "error": f"Tool '{name}' not found",
            "available_tools": list(TOOLS.keys())
        }

    try:
        result = TOOLS[name](**kwargs)
        _log_tool_call(name, kwargs, result, caller)
        return result
    except Exception as e:
        return {
            "error": str(e),
            "tool": name,
            "inputs": kwargs
        }


def get_audit_log() -> list:
    return _audit_log.copy()


def clear_audit_log():
    global _audit_log
    _audit_log = []


def list_tools() -> Dict[str, Dict]:
    return {
        name: {"available": True, **TOOL_METADATA.get(name, {})}
        for name in TOOLS.keys()
    }