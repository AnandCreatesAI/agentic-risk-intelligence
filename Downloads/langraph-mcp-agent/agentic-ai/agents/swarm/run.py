from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from agents.swarm.anomaly import anomaly_agent
from agents.swarm.similarity import similarity_agent
from agents.swarm.pattern import pattern_agent

logger = logging.getLogger("Swarm")

SWARM_AGENTS = {
    "anomaly": anomaly_agent,
    "similarity": similarity_agent,
    "pattern": pattern_agent
}


def run_swarm(declaration: Dict[str, Any], agents: List[str] = None) -> List[Dict[str, Any]]:
    agent_names = agents or list(SWARM_AGENTS.keys())
    agent_names = [a for a in agent_names if a in SWARM_AGENTS]

    if not agent_names:
        return []

    signals: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=len(agent_names)) as executor:
        future_to_name = {
            executor.submit(SWARM_AGENTS[name], declaration): name
            for name in agent_names
        }

        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                result = future.result()
                result["agent"] = name
                signals.append(result)
            except Exception as e:
                signals.append({
                    "agent": name,
                    "type": name,
                    "score": 0.0,
                    "confidence": 0.0,
                    "error": str(e),
                    "evidence": []
                })

    return signals


def run_targeted_swarm(declaration: Dict[str, Any], risk_areas: List[str]) -> List[Dict[str, Any]]:
    mapping = {
        "anomaly": "anomaly",
        "historical": "similarity",
        "pattern": "pattern",
        "behavioral": "anomaly",
        "structuring": "pattern"
    }

    agents = list({mapping.get(area, area) for area in risk_areas})
    return run_swarm(declaration, agents=agents)