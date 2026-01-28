# main.py
# Run the Agentic Risk Intelligence System
# 
# This demonstrates the complete workflow:
# 1. Planner decides what checks are needed
# 2. Swarm agents explore for risk signals in parallel
# 3. Specialist agents verify facts (sanctions, etc.)
# 4. Aggregator combines signals into a risk decision
# 5. Explainer generates human-readable explanation

import os
import json
import logging
from dotenv import load_dotenv

# Load environment variables (for LangSmith API key)
load_dotenv()

from workflows.risk_graph import run_assessment, get_decision, get_explanation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# ============================================================================
# LANGSMITH SETUP (Optional but recommended)
# ============================================================================

def setup_observability():
    """
    Configure LangSmith for tracing and monitoring.
    
    To enable:
    1. Get API key from https://smith.langchain.com
    2. Set environment variables:
       export LANGCHAIN_TRACING_V2=true
       export LANGCHAIN_API_KEY=your-api-key
       export LANGCHAIN_PROJECT=agentic-risk-intelligence
    """
    try:
        from observability import setup_langsmith, LANGSMITH_AVAILABLE
        
        if LANGSMITH_AVAILABLE and os.environ.get("LANGCHAIN_API_KEY"):
            setup_langsmith(project_name="agentic-risk-intelligence")
            print("✅ LangSmith tracing enabled - view traces at https://smith.langchain.com")
            return True
        else:
            print("ℹ️  LangSmith not configured (set LANGCHAIN_API_KEY to enable)")
            return False
    except ImportError:
        print("ℹ️  LangSmith not installed (pip install langsmith)")
        return False


def print_separator(title: str = ""):
    """Print a visual separator."""
    print("\n" + "=" * 70)
    if title:
        print(f"  {title}")
        print("=" * 70)


def run_example(declaration: dict, name: str = "Example"):
    """Run a single assessment and display results."""
    print_separator(f"ASSESSMENT: {name}")
    print(f"\nInput Declaration:")
    print(json.dumps(declaration, indent=2))
    
    # Run the assessment
    result = run_assessment(declaration)
    
    # Display planning info
    print_separator("PLANNING")
    print(f"Tasks identified: {result.get('tasks', [])}")
    print(f"Swarm agents: {result.get('swarm_agents', [])}")
    print(f"Initial risk factors: {result.get('risk_factors', [])}")
    
    # Display signals
    print_separator("SIGNALS")
    for signal in result.get("signals", []):
        print(f"\n[{signal.get('type', 'unknown').upper()}]")
        print(f"  Score: {signal.get('score', 0):.2f}")
        print(f"  Confidence: {signal.get('confidence', 0):.2f}")
        if signal.get("evidence"):
            print(f"  Evidence: {len(signal['evidence'])} items")
    
    # Display specialist results
    print_separator("SPECIALIST VERIFICATION")
    specialist_results = result.get("specialist_results", {})
    if specialist_results:
        for name, res in specialist_results.items():
            print(f"\n[{name.upper()}]")
            print(f"  Verified: {res.get('verified', False)}")
            print(f"  Hit: {res.get('hit', False)}")
            if res.get("risk_indicators"):
                for indicator in res["risk_indicators"]:
                    print(f"  ⚠️  {indicator}")
    else:
        print("No specialist checks performed.")
    
    # Display decision
    decision = get_decision(result)
    print_separator("DECISION")
    print(f"\n🎯 RISK SCORE: {decision.get('risk_score', 0):.1%}")
    print(f"📊 RISK LEVEL: {decision.get('risk_level', 'UNKNOWN')}")
    print(f"✅ DECISION: {decision.get('decision', 'UNKNOWN')}")
    print(f"\n📝 Reason: {decision.get('decision_reason', 'N/A')}")
    
    # Display contributing factors
    factors = decision.get("contributing_factors", [])
    if factors:
        print(f"\n📋 Contributing Factors ({len(factors)}):")
        for factor in factors[:5]:
            severity = factor.get("severity", "?")
            emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity, "⚪")
            print(f"  {emoji} [{severity}] {factor.get('factor', 'Unknown')}")
    
    # Display full explanation
    print_separator("FULL EXPLANATION")
    print(get_explanation(result))
    
    return result


def main():
    """Run multiple example assessments."""
    
    # Setup LangSmith observability (optional)
    setup_observability()
    
    # ========================================
    # Example 1: High-Risk Transaction
    # Country is sanctioned, high value
    # ========================================
    high_risk_declaration = {
        "company": "ABC Corp",
        "country": "IR",  # Iran - sanctioned
        "value": 2_000_000
    }
    run_example(high_risk_declaration, "High-Risk (Sanctioned Country + High Value)")
    
    # ========================================
    # Example 2: Medium-Risk Transaction
    # High value, but safe country
    # ========================================
    medium_risk_declaration = {
        "company": "Global Trading LLC",
        "country": "GB",  # UK - safe
        "value": 1_500_000
    }
    run_example(medium_risk_declaration, "Medium-Risk (High Value, Safe Country)")
    
    # ========================================
    # Example 3: Low-Risk Transaction
    # Normal value, safe country
    # ========================================
    low_risk_declaration = {
        "company": "Acme Industries",
        "country": "US",
        "value": 50_000
    }
    run_example(low_risk_declaration, "Low-Risk (Normal Transaction)")
    
    # ========================================
    # Example 4: Sanctioned Company
    # Direct match on sanctions list
    # ========================================
    sanctioned_company = {
        "company": "Evil Corp International",
        "country": "US",
        "value": 100_000
    }
    run_example(sanctioned_company, "Critical-Risk (Sanctioned Company)")
    
    print_separator("ASSESSMENT COMPLETE")
    print("\n✅ All assessments completed successfully!")
    print("See above for detailed risk analysis for each transaction.\n")
    
    # Show LangSmith link if enabled
    if os.environ.get("LANGCHAIN_API_KEY"):
        project = os.environ.get("LANGCHAIN_PROJECT", "agentic-risk-intelligence")
        print(f"📊 View traces at: https://smith.langchain.com/o/default/projects/p/{project}")


if __name__ == "__main__":
    main()
