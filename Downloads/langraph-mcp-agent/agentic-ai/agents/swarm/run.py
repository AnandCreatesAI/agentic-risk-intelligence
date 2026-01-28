# agents/swarm/run.py
# Swarm Orchestrator
# Runs all swarm agents in parallel and collects their signals.
# Swarm produces signals, NOT decisions.

from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from agents.swarm.anamoly import anomaly_agent
from agents.swarm.similarity import similarity_agent
from agents.swarm.pattern import pattern_agent

logger = logging.getLogger("Swarm")


# Registry of all swarm agents
SWARM_AGENTS = {
    "anomaly": anomaly_agent,
    "similarity": similarity_agent,
    "pattern": pattern_agent
}


def run_swarm(declaration: Dict[str, Any], agents: List[str] = None) -> List[Dict[str, Any]]:
    """
    Run swarm agents in parallel to detect risk signals.
    
    The swarm model allows for:
    - Parallel exploration of different risk dimensions
    - Independent, isolated agent execution
    - Signal aggregation without agent coordination
    
    Args:
        declaration: The input data to analyze
        agents: Optional list of specific agents to run (defaults to all)
        
    Returns:
        List of signal dictionaries from all agents
    """
    # Determine which agents to run
    if agents is None:
        agents_to_run = list(SWARM_AGENTS.values())
        agent_names = list(SWARM_AGENTS.keys())
    else:
        agents_to_run = [SWARM_AGENTS[name] for name in agents if name in SWARM_AGENTS]
        agent_names = [name for name in agents if name in SWARM_AGENTS]
    
    if not agents_to_run:
        logger.warning("No valid swarm agents specified")
        return []
    
    signals = []
    
    # Run agents in parallel
    logger.info(f"Running swarm with agents: {agent_names}")
    
    with ThreadPoolExecutor(max_workers=len(agents_to_run)) as executor:
        # Submit all agents
        future_to_agent = {
            executor.submit(agent, declaration): name 
            for agent, name in zip(agents_to_run, agent_names)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_agent):
            agent_name = future_to_agent[future]
            try:
                result = future.result()
                result["agent"] = agent_name
                signals.append(result)
                logger.info(f"Agent {agent_name} completed: score={result.get('score', 'N/A')}")
            except Exception as e:
                logger.error(f"Agent {agent_name} failed: {e}")
                signals.append({
                    "agent": agent_name,
                    "type": agent_name,
                    "score": 0.0,
                    "confidence": 0.0,
                    "error": str(e),
                    "evidence": []
                })
    
    return signals


def run_targeted_swarm(declaration: Dict[str, Any], risk_areas: List[str]) -> List[Dict[str, Any]]:
    """
    Run only specific swarm agents based on identified risk areas.
    
    This allows the planner to target exploration based on initial assessment.
    
    Args:
        declaration: The input data to analyze
        risk_areas: Areas to investigate (maps to agent types)
        
    Returns:
        List of signals from targeted agents
    """
    # Map risk areas to agents
    area_to_agent = {
        "anomaly": "anomaly",
        "historical": "similarity",
        "pattern": "pattern",
        "behavioral": "anomaly",
        "structuring": "pattern"
    }
    
    agents = list(set(area_to_agent.get(area, area) for area in risk_areas))
    return run_swarm(declaration, agents=agents)
