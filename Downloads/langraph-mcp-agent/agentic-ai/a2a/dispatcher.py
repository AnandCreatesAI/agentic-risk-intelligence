# a2a/dispatcher.py
# A2A Message Dispatcher
# Routes messages between agents and coordinates with MCP tools.
# Ensures all inter-agent communication is structured and auditable.

from typing import Dict, Any, Optional, Callable
from datetime import datetime
import logging

from a2a.messages import MessageType, result, validate_message
from mcp.server import call_tool

logger = logging.getLogger("A2A")


# ============================================================================
# MESSAGE HANDLERS
# ============================================================================

def _handle_sanctions_check(message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle sanctions check task."""
    payload = message["content"]["payload"]
    
    tool_result = call_tool(
        "check_sanctions",
        caller=message["sender"],
        company=payload.get("company", ""),
        country=payload.get("country")
    )
    
    return result(
        sender="sanctions_agent",
        receiver=message["sender"],
        task_name="sanctions_check",
        data=tool_result,
        success=True,
        correlation_id=message.get("correlation_id")
    )


def _handle_similarity_search(message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle similarity search task."""
    payload = message["content"]["payload"]
    
    tool_result = call_tool(
        "search_similar_cases",
        caller=message["sender"],
        company=payload.get("company", ""),
        country=payload.get("country", ""),
        value=payload.get("value", 0)
    )
    
    return result(
        sender="similarity_agent",
        receiver=message["sender"],
        task_name="similarity_search",
        data=tool_result,
        success=True,
        correlation_id=message.get("correlation_id")
    )


def _handle_anomaly_detection(message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle anomaly detection task."""
    payload = message["content"]["payload"]
    
    tool_result = call_tool(
        "detect_anomalies",
        caller=message["sender"],
        value=payload.get("value", 0),
        country=payload.get("country", ""),
        company=payload.get("company", "")
    )
    
    return result(
        sender="anomaly_agent",
        receiver=message["sender"],
        task_name="anomaly_detection",
        data=tool_result,
        success=True,
        correlation_id=message.get("correlation_id")
    )


def _handle_pattern_check(message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle pattern detection task."""
    payload = message["content"]["payload"]
    
    tool_result = call_tool(
        "check_patterns",
        caller=message["sender"],
        company=payload.get("company", ""),
        country=payload.get("country", ""),
        value=payload.get("value", 0)
    )
    
    return result(
        sender="pattern_agent",
        receiver=message["sender"],
        task_name="pattern_check",
        data=tool_result,
        success=True,
        correlation_id=message.get("correlation_id")
    )


def _handle_company_lookup(message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle company information lookup."""
    payload = message["content"]["payload"]
    
    tool_result = call_tool(
        "get_company_info",
        caller=message["sender"],
        company=payload.get("company", "")
    )
    
    return result(
        sender="registry_agent",
        receiver=message["sender"],
        task_name="company_lookup",
        data=tool_result,
        success=True,
        correlation_id=message.get("correlation_id")
    )


# Task router
TASK_HANDLERS: Dict[str, Callable] = {
    "sanctions_check": _handle_sanctions_check,
    "similarity_search": _handle_similarity_search,
    "anomaly_detection": _handle_anomaly_detection,
    "pattern_check": _handle_pattern_check,
    "company_lookup": _handle_company_lookup,
}


# ============================================================================
# DISPATCHER
# ============================================================================

# Message log for audit
_message_log = []


def dispatch(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dispatch an A2A message to the appropriate handler.
    
    Args:
        message: A2A message to dispatch
        
    Returns:
        Result message from the handler
    """
    # Validate message
    try:
        validate_message(message)
    except ValueError as e:
        logger.error(f"Invalid message: {e}")
        return {
            "error": str(e),
            "original_message": message
        }
    
    # Log incoming message
    _message_log.append({
        "direction": "incoming",
        "timestamp": datetime.now().isoformat(),
        "message": message
    })
    
    # Route based on message type
    if message["type"] == MessageType.TASK.value:
        task_name = message["content"].get("task")
        
        if task_name not in TASK_HANDLERS:
            error_msg = f"Unknown task: {task_name}"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "available_tasks": list(TASK_HANDLERS.keys())
            }
        
        # Execute handler
        response = TASK_HANDLERS[task_name](message)
        
        # Log response
        _message_log.append({
            "direction": "outgoing",
            "timestamp": datetime.now().isoformat(),
            "message": response
        })
        
        logger.info(f"Dispatched task: {task_name} from {message['sender']}")
        return response
    
    else:
        return {
            "error": f"Dispatcher does not handle message type: {message['type']}",
            "message": message
        }


def dispatch_batch(messages: list) -> list:
    """
    Dispatch multiple messages (for parallel execution).
    
    Args:
        messages: List of A2A messages
        
    Returns:
        List of results
    """
    return [dispatch(msg) for msg in messages]


def get_message_log() -> list:
    """Get the message audit log."""
    return _message_log.copy()


def clear_message_log():
    """Clear message log (for testing)."""
    global _message_log
    _message_log = []
