import json
import logging
from workflows.risk_graph import run_assessment, get_decision, get_explanation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def run_example(declaration: dict):
    result = run_assessment(declaration)

    decision = get_decision(result)
    explanation = get_explanation(result)

    output = {
        "input": declaration,
        "tasks": result.get("tasks"),
        "swarm_agents": result.get("swarm_agents"),
        "signals": result.get("signals"),
        "specialist_results": result.get("specialist_results"),
        "decision": decision,
        "explanation": explanation
    }

    print(json.dumps(output, indent=2))
    return result


def main():
    examples = [
        {
            "company": "ABC Corp",
            "country": "IR",
            "value": 2_000_000
        },
        {
            "company": "Global Trading LLC",
            "country": "GB",
            "value": 1_500_000
        },
        {
            "company": "Acme Industries",
            "country": "US",
            "value": 50_000
        },
        {
            "company": "Evil Corp International",
            "country": "US",
            "value": 100_000
        }
    ]

    for example in examples:
        run_example(example)


if __name__ == "__main__":
    main()