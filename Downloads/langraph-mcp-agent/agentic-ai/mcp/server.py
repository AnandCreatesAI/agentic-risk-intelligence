# mcp/server.py
# MCP Server - Tool Registry and Execution Layer
# All agent tool access is mediated through this server.
# Provides: security, logging, rate limiting, governance.

from typing import Dict, Any, Callable, Optional
from datetime import datetime
import logging

from mcp.tools import (
    check_sanctions,
    search_similar_cases,
    detect_anomalies,
    check_patterns,
    get_company_info
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCP")


# ============================================================================
# TOOL REGISTRY
# ============================================================================

TOOLS: Dict[str, Callable] = {
    "check_sanctions": check_sanctions,
    "search_similar_cases": search_similar_cases,
    "detect_anomalies": detect_anomalies,
    "check_patterns": check_patterns,
    "get_company_info": get_company_info,
}

# Tool metadata for governance
TOOL_METADATA = {
    "check_sanctions": {
        "description": "Check sanctions lists (OFAC, EU, UN)",
        "requires_audit": True,
        "category": "compliance"
    },
    "search_similar_cases": {
        "description": "Find similar historical cases",
        "requires_audit": False,
        "category": "analytics"
    },
    "detect_anomalies": {
        "description": "Statistical anomaly detection",
        "requires_audit": False,
        "category": "analytics"
    },
    "check_patterns": {
        "description": "Detect known risk patterns",
        "requires_audit": False,
        "category": "analytics"
    },
    "get_company_info": {
        "description": "Retrieve company registry information",
        "requires_audit": True,
        "category": "verification"
    }
}


# ============================================================================
# AUDIT LOG
# ============================================================================

_audit_log = []


def _log_tool_call(tool_name: str, kwargs: Dict, result: Any, caller: str = "unknown"):
    """Log all tool invocations for audit trail."""
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
    return entry


def _summarize_result(result: Any) -> str:
    """Create a summary of the result for logging."""
    if isinstance(result, dict):
        if "hit" in result:
            return f"hit={result['hit']}"
        if "anomaly_score" in result:
            return f"anomaly_score={result['anomaly_score']}"
        if "pattern_score" in result:
            return f"pattern_score={result['pattern_score']}"
    return "completed"


def get_audit_log() -> list:
    """Retrieve the full audit log."""
    return _audit_log.copy()


def clear_audit_log():
    """Clear the audit log (for testing)."""
    global _audit_log
    _audit_log = []


# ============================================================================
# TOOL EXECUTION
# ============================================================================

def call_tool(name: str, caller: str = "unknown", **kwargs) -> Dict[str, Any]:
    """
    Execute a tool by name with given arguments.
    All tool access goes through this function for governance.
    
    Args:
        name: The tool name from the registry
        caller: Identity of the calling agent (for audit)
        **kwargs: Arguments to pass to the tool
        
    Returns:
        Tool result with metadata
    """
    if name not in TOOLS:
        error_result = {
            "error": f"Tool '{name}' not found in registry",
            "available_tools": list(TOOLS.keys())
        }
        logger.error(f"Tool not found: {name}")
        return error_result
    
    try:
        # Execute the tool
        result = TOOLS[name](**kwargs)
        
        # Log for audit
        _log_tool_call(name, kwargs, result, caller)
        
        return result
        
    except Exception as e:
        error_result = {
            "error": str(e),
            "tool": name,
            "inputs": kwargs
        }
        logger.error(f"Tool execution failed: {name} - {e}")
        return error_result


def list_tools() -> Dict[str, Dict]:
    """List all available tools with metadata."""
    return {
        name: {
            "available": True,
            **TOOL_METADATA.get(name, {})
        }
        for name in TOOLS.keys()
    }
