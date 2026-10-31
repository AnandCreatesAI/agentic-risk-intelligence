from typing import Dict, Any, Callable
from datetime import datetime
import logging

from a2a.messages import MessageType, result, validate_message
from mcp.server import call_tool

logger = logging.getLogger("A2A")

def _handle_sanctions_check(message: Dict[str, Any]) -> Dict[str, Any]:
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


TASK_HANDLERS: Dict[str, Callable] = {
    "sanctions_check": _handle_sanctions_check,
    "similarity_search": _handle_similarity_search,
    "anomaly_detection": _handle_anomaly_detection,
    "pattern_check": _handle_pattern_check,
}


_message_log = []


def dispatch(message: Dict[str, Any]) -> Dict[str, Any]:
    try:
        validate_message(message)
    except ValueError as e:
        return {"error": str(e), "original_message": message}

    _message_log.append({
        "direction": "incoming",
        "timestamp": datetime.now().isoformat(),
        "message": message
    })

    if message["type"] == MessageType.TASK.value:
        task_name = message["content"].get("task")

        if task_name not in TASK_HANDLERS:
            return {
                "error": f"Unknown task: {task_name}",
                "available_tasks": list(TASK_HANDLERS.keys())
            }

        response = TASK_HANDLERS[task_name](message)

        _message_log.append({
            "direction": "outgoing",
            "timestamp": datetime.now().isoformat(),
            "message": response
        })

        return response

    return {
        "error": f"Unsupported message type: {message['type']}",
        "message": message
    }


def dispatch_batch(messages: list) -> list:
    return [dispatch(message) for message in messages]


def get_message_log() -> list:
    return _message_log.copy()


def clear_message_log():
    global _message_log
    _message_log = []