import requests
from typing import Dict, Any, List
from datetime import datetime

LLM_URL = "http://69.19.137.143:8080/v1/chat/completions"
LLM_API_KEY = "57c2bbc0bfeffd04b71409641170c7f900f383d65cf76cb4569e738f6c8bf932"
LLM_MODEL = "llama4-scout"


def _call_llm(messages: List[Dict[str, str]]) -> str:
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": 0.2
    }

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(LLM_URL, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def explanation_node_llm(state: Dict[str, Any]) -> Dict[str, Any]:
    decision = state.get("decision", {})
    signals = state.get("signals", [])
    specialist_results = state.get("specialist_results", {})
    input_data = state.get("input", {})

    evidence_lines = []
    for s in signals:
        evidence_lines.append(f"{s.get('type')} score={s.get('score')}")
        for ev in s.get("evidence", [])[:2]:
            evidence_lines.append(f"- {ev.get('description', ev.get('type'))}")

    sanctions = specialist_results.get("sanctions", {})
    specialist_lines = []
    if sanctions.get("verified"):
        specialist_lines.append(f"Sanctions hit: {sanctions.get('hit')}")

    messages = [
        {
            "role": "system",
            "content": "You are a compliance risk analyst generating professional risk assessment explanations."
        },
        {
            "role": "user",
            "content": f"""
Transaction:
Company: {input_data.get('company')}
Country: {input_data.get('country')}
Value: {input_data.get('value')}

Decision:
Risk Score: {decision.get('risk_score')}
Risk Level: {decision.get('risk_level')}
Decision: {decision.get('decision')}
Reason: {decision.get('decision_reason')}

Evidence:
{chr(10).join(evidence_lines)}

Specialist:
{chr(10).join(specialist_lines)}

Provide:
1. Executive summary
2. Key risk factors
3. Recommended actions
4. Confidence assessment
"""
        }
    ]

    try:
        narrative = _call_llm(messages)
        generator = "llama4-scout"
    except Exception as e:
        narrative = f"LLM generation failed: {e}"
        generator = "fallback"

    state["explanation"] = {
        "timestamp": datetime.now().isoformat(),
        "generated_by": generator,
        "risk_assessment": decision,
        "full_narrative": narrative
    }

    return state