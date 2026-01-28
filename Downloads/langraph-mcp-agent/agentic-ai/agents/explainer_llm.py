# agents/explainer_llm.py
# LLM-Powered Explanation Agent
# Uses GPT to generate natural language explanations from structured signals.
# Falls back to template-based explanation if LLM unavailable.

import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger("ExplainerLLM")

# Try to import LangChain OpenAI
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("langchain-openai not installed. Using template-based explanations.")


# ============================================================================
# LLM CONFIGURATION
# ============================================================================

def get_llm(model: str = "gpt-4o-mini", temperature: float = 0.3) -> Optional["ChatOpenAI"]:
    """Get configured LLM instance."""
    if not LLM_AVAILABLE:
        return None
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set. LLM explanations disabled.")
        return None
    
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key
    )


# ============================================================================
# PROMPT TEMPLATE
# ============================================================================

EXPLANATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a compliance risk analyst generating clear, professional risk assessment reports.

Your task is to explain a risk decision in plain language that:
1. A compliance officer can understand and act on
2. A regulator would find satisfactory for audit purposes
3. Clearly states the decision and key reasons

Be concise but thorough. Use professional language. Do not use emojis."""),
    
    ("human", """Generate a risk assessment explanation for this transaction:

**Transaction Details:**
- Company: {company}
- Country: {country}
- Value: ${value:,.0f}

**Decision:**
- Risk Score: {risk_score:.1%}
- Risk Level: {risk_level}
- Final Decision: {decision}
- Reason: {decision_reason}

**Key Evidence:**
{evidence_summary}

**Specialist Findings:**
{specialist_summary}

Please provide:
1. An executive summary (2-3 sentences)
2. Key risk factors identified
3. Recommended actions
4. Confidence assessment""")
])


# ============================================================================
# LLM-POWERED EXPLANATION
# ============================================================================

def explanation_node_llm(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate explanation using LLM (with fallback to templates).
    
    This provides more natural, context-aware explanations while
    maintaining the structured evidence trail from the rule-based system.
    """
    decision = state.get("decision", {})
    signals = state.get("signals", [])
    specialist_results = state.get("specialist_results", {})
    input_data = state.get("input", {})
    
    # Get LLM
    llm = get_llm()
    
    if llm:
        # Use LLM for natural explanation
        explanation = _generate_llm_explanation(
            llm, input_data, decision, signals, specialist_results
        )
    else:
        # Fallback to template-based
        from agents.explainer import explanation_node
        return explanation_node(state)
    
    # Build structured explanation with LLM narrative
    state["explanation"] = {
        "timestamp": datetime.now().isoformat(),
        "generated_by": "llm" if llm else "template",
        "executive_summary": explanation.get("summary", ""),
        "risk_assessment": {
            "score": decision.get("risk_score", 0),
            "level": decision.get("risk_level", "UNKNOWN"),
            "decision": decision.get("decision", "UNKNOWN")
        },
        "evidence_trail": _build_evidence_trail(signals, specialist_results),
        "confidence": _assess_confidence(signals, specialist_results),
        "recommendations": explanation.get("recommendations", []),
        "full_narrative": explanation.get("full_narrative", "")
    }
    
    return state


def _generate_llm_explanation(
    llm: "ChatOpenAI",
    input_data: Dict,
    decision: Dict,
    signals: List[Dict],
    specialist_results: Dict
) -> Dict[str, Any]:
    """Generate explanation using LLM."""
    
    # Build evidence summary for prompt
    evidence_lines = []
    for signal in signals:
        signal_type = signal.get("type", "unknown")
        score = signal.get("score", 0)
        evidence_lines.append(f"- {signal_type.title()} Analysis: Score {score:.2f}")
        for ev in signal.get("evidence", [])[:2]:  # Top 2 evidence items
            evidence_lines.append(f"  - {ev.get('description', ev.get('type', 'N/A'))}")
    
    evidence_summary = "\n".join(evidence_lines) if evidence_lines else "No significant signals detected."
    
    # Build specialist summary
    specialist_lines = []
    sanctions = specialist_results.get("sanctions", {})
    if sanctions.get("verified"):
        specialist_lines.append(f"- Sanctions Check: {'HIT' if sanctions.get('hit') else 'CLEAR'}")
        for indicator in sanctions.get("risk_indicators", []):
            specialist_lines.append(f"  - {indicator}")
    
    specialist_summary = "\n".join(specialist_lines) if specialist_lines else "No specialist checks performed."
    
    # Build the chain
    chain = EXPLANATION_PROMPT | llm | StrOutputParser()
    
    try:
        # Invoke LLM
        llm_response = chain.invoke({
            "company": input_data.get("company", "Unknown"),
            "country": input_data.get("country", "Unknown"),
            "value": input_data.get("value", 0),
            "risk_score": decision.get("risk_score", 0),
            "risk_level": decision.get("risk_level", "UNKNOWN"),
            "decision": decision.get("decision", "UNKNOWN"),
            "decision_reason": decision.get("decision_reason", "N/A"),
            "evidence_summary": evidence_summary,
            "specialist_summary": specialist_summary
        })
        
        logger.info("LLM explanation generated successfully")
        
        return {
            "summary": _extract_summary(llm_response),
            "recommendations": _extract_recommendations(llm_response),
            "full_narrative": llm_response
        }
        
    except Exception as e:
        logger.error(f"LLM explanation failed: {e}")
        return {
            "summary": f"Risk assessment: {decision.get('decision', 'UNKNOWN')}",
            "recommendations": [],
            "full_narrative": f"LLM explanation failed: {e}"
        }


def _extract_summary(text: str) -> str:
    """Extract executive summary from LLM response."""
    lines = text.split("\n")
    summary_lines = []
    in_summary = False
    
    for line in lines:
        if "executive summary" in line.lower() or "summary" in line.lower():
            in_summary = True
            continue
        if in_summary:
            if line.strip() and not line.startswith("#") and not line.startswith("**"):
                summary_lines.append(line.strip())
            if len(summary_lines) >= 3 or (line.startswith("#") or line.startswith("**")):
                break
    
    return " ".join(summary_lines) if summary_lines else text[:500]


def _extract_recommendations(text: str) -> List[str]:
    """Extract recommendations from LLM response."""
    recommendations = []
    lines = text.split("\n")
    in_recommendations = False
    
    for line in lines:
        if "recommend" in line.lower() and ("action" in line.lower() or ":" in line):
            in_recommendations = True
            continue
        if in_recommendations:
            line = line.strip()
            if line.startswith(("-", "•", "*")) or (line and line[0].isdigit()):
                rec = line.lstrip("-•* 0123456789.)")
                if rec:
                    recommendations.append(rec)
            elif line.startswith("#") or line.startswith("**"):
                break
    
    return recommendations[:5]  # Max 5 recommendations


def _build_evidence_trail(signals: List[Dict], specialist_results: Dict) -> List[Dict]:
    """Build structured evidence trail (same as template version)."""
    evidence = []
    
    for signal in signals:
        signal_type = signal.get("type", "unknown")
        for item in signal.get("evidence", []):
            evidence.append({
                "source": f"Swarm Analysis ({signal_type})",
                "type": item.get("type", "observation"),
                "finding": item.get("description", str(item)),
                "severity": item.get("severity", "INFO")
            })
    
    sanctions = specialist_results.get("sanctions", {})
    if sanctions.get("verified"):
        for item in sanctions.get("evidence", []):
            evidence.append({
                "source": "Sanctions Verification",
                "type": item.get("type", "verification"),
                "finding": f"{item.get('type', 'Hit')}: {item.get('entity', item.get('country', 'Unknown'))}",
                "severity": item.get("severity", "HIGH")
            })
    
    return evidence


def _assess_confidence(signals: List[Dict], specialist_results: Dict) -> Dict:
    """Assess confidence (same as template version)."""
    confidences = [s.get("confidence", 0.5) for s in signals]
    
    if specialist_results.get("sanctions", {}).get("verified"):
        confidences.append(0.95)
    
    avg = sum(confidences) / max(len(confidences), 1)
    
    if avg >= 0.8:
        level, desc = "HIGH", "Decision supported by strong evidence"
    elif avg >= 0.6:
        level, desc = "MEDIUM", "Moderate evidence; review may be warranted"
    else:
        level, desc = "LOW", "Limited evidence; manual review recommended"
    
    return {"level": level, "score": round(avg, 2), "description": desc}
