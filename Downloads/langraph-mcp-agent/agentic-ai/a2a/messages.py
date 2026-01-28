# a2a/messages.py
# Agent-to-Agent Message Protocol
# Defines structured message formats for agent communication.
# Prevents free-form chat and ensures auditable, contract-driven interactions.

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import uuid


class MessageType(Enum):
    """Types of A2A messages."""
    TASK = "task"           # Request to perform a task
    RESULT = "result"       # Result of a task
    SIGNAL = "signal"       # Risk signal (from swarm)
    QUERY = "query"         # Information request
    RESPONSE = "response"   # Response to query


class Priority(Enum):
    """Message priority levels."""
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
    """
    Create a standardized A2A message.
    
    Args:
        msg_type: Type of message
        sender: Sending agent identifier
        receiver: Receiving agent identifier
        content: Message payload
        priority: Message priority
        correlation_id: ID to correlate related messages
        
    Returns:
        Structured message dictionary
    """
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
    """
    Create a task message - request an agent to perform work.
    
    Args:
        sender: Requesting agent
        receiver: Agent to perform the task
        name: Task name/identifier
        payload: Task parameters
        priority: Task priority
        
    Returns:
        Task message
    """
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
    """
    Create a result message - response to a task.
    
    Args:
        sender: Agent that performed the task
        receiver: Agent that requested the task
        task_name: Name of completed task
        data: Result data
        success: Whether task succeeded
        correlation_id: ID of original task message
        
    Returns:
        Result message
    """
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
    """
    Create a signal message - risk indicator from swarm agents.
    
    Args:
        sender: Swarm agent producing the signal
        signal_type: Type of signal (anomaly, similarity, pattern)
        score: Risk score (0.0 to 1.0)
        evidence: Supporting evidence
        confidence: Confidence in the signal (0.0 to 1.0)
        
    Returns:
        Signal message
    """
    return create_message(
        msg_type=MessageType.SIGNAL,
        sender=sender,
        receiver="aggregator",  # Signals always go to aggregator
        content={
            "signal_type": signal_type,
            "score": score,
            "confidence": confidence,
            "evidence": evidence
        }
    )


def validate_message(msg: Dict[str, Any]) -> bool:
    """
    Validate that a message has required fields.
    
    Args:
        msg: Message to validate
        
    Returns:
        True if valid, raises ValueError if not
    """
    required_fields = ["id", "type", "timestamp", "sender", "receiver", "content"]
    
    for field in required_fields:
        if field not in msg:
            raise ValueError(f"Message missing required field: {field}")
    
    if msg["type"] not in [mt.value for mt in MessageType]:
        raise ValueError(f"Invalid message type: {msg['type']}")
    
    return True
