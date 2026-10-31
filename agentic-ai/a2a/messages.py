from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import uuid


class MessageType(Enum):
    TASK = "task"
    RESULT = "result"
    SIGNAL = "signal"
    QUERY = "query"
    RESPONSE = "response"


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def create_message(
    msg_type: MessageType,
    sender: str,
    receiver: str,
    content: Dict[str, Any],
    priority: Priority = Priority.MEDIUM,
    correlation_id: Optional[str] = None
) -> Dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "type": msg_type.value,
        "timestamp": datetime.now().isoformat(),
        "sender": sender,
        "receiver": receiver,
        "priority": priority.value,
        "correlation_id": correlation_id or str(uuid.uuid4()),
        "content": content
    }


def task(
    sender: str,
    receiver: str,
    name: str,
    payload: Dict[str, Any],
    priority: Priority = Priority.MEDIUM
) -> Dict[str, Any]:
    return create_message(
        msg_type=MessageType.TASK,
        sender=sender,
        receiver=receiver,
        content={
            "task": name,
            "payload": payload
        },
        priority=priority
    )


def result(
    sender: str,
    receiver: str,
    task_name: str,
    data: Dict[str, Any],
    success: bool = True,
    correlation_id: Optional[str] = None
) -> Dict[str, Any]:
    return create_message(
        msg_type=MessageType.RESULT,
        sender=sender,
        receiver=receiver,
        content={
            "task": task_name,
            "success": success,
            "data": data
        },
        correlation_id=correlation_id
    )


def signal(
    sender: str,
    signal_type: str,
    score: float,
    evidence: List[Dict[str, Any]],
    confidence: float = 1.0
) -> Dict[str, Any]:
    return create_message(
        msg_type=MessageType.SIGNAL,
        sender=sender,
        receiver="aggregator",
        content={
            "signal_type": signal_type,
            "score": score,
            "confidence": confidence,
            "evidence": evidence
        }
    )


def validate_message(msg: Dict[str, Any]) -> bool:
    required = ["id", "type", "timestamp", "sender", "receiver", "content"]

    for field in required:
        if field not in msg:
            raise ValueError(f"Missing field: {field}")

    if msg["type"] not in [t.value for t in MessageType]:
        raise ValueError(f"Invalid message type: {msg['type']}")

    return True