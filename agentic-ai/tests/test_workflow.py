import pytest
from workflows.risk_graph import run_assessment, get_decision
from mcp.server import call_tool


class TestWorkflow:

    def test_high_risk_transaction(self):
        declaration = {
            "company": "ABC Corp",
            "country": "IR",
            "value": 2_000_000
        }

        result = run_assessment(declaration)
        decision = get_decision(result)

        assert decision["risk_level"] in ["HIGH", "CRITICAL"]
        assert decision["decision"] in ["BLOCK", "FLAG"]
        assert decision["risk_score"] > 0.5

    def test_low_risk_transaction(self):
        declaration = {
            "company": "Acme Industries",
            "country": "US",
            "value": 50_000
        }

        result = run_assessment(declaration)
        decision = get_decision(result)

        assert decision["risk_level"] == "LOW"
        assert decision["decision"] == "APPROVE"
        assert decision["risk_score"] < 0.4

    def test_planner_identifies_tasks(self):
        declaration = {
            "company": "Test Corp",
            "country": "IR",
            "value": 1_500_000
        }

        result = run_assessment(declaration)

        assert "sanctions_check" in result["tasks"]
        assert "high_value_review" in result["tasks"]

    def test_signals_generated(self):
        declaration = {
            "company": "Test Corp",
            "country": "GB",
            "value": 500_000
        }

        result = run_assessment(declaration)

        assert len(result["signals"]) > 0
        for signal in result["signals"]:
            assert "type" in signal
            assert "score" in signal

    def test_explanation_generated(self):
        declaration = {
            "company": "Test Corp",
            "country": "US",
            "value": 100_000
        }

        result = run_assessment(declaration)

        assert "explanation" in result
        assert result["explanation"] is not None


class TestSanctions:

    def test_sanctioned_country_detected(self):
        result = call_tool(
            "check_sanctions",
            caller="test",
            company="Test Corp",
            country="IR"
        )

        assert result["country_hit"] is True
        assert result["hit"] is True

    def test_clean_country_passes(self):
        result = call_tool(
            "check_sanctions",
            caller="test",
            company="Test Corp",
            country="US"
        )

        assert result["country_hit"] is False


class TestAnomalyDetection:

    def test_high_value_anomaly(self):
        result = call_tool(
            "detect_anomalies",
            caller="test",
            value=10_000_000,
            country="US",
            company="Test"
        )

        assert result["is_anomalous"] is True
        assert result["anomaly_score"] > 0.5

    def test_normal_value_passes(self):
        result = call_tool(
            "detect_anomalies",
            caller="test",
            value=200_000,
            country="US",
            company="Test"
        )

        assert result["anomaly_score"] < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])