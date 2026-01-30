# tests/test_workflow.py
"""
Tests for the Risk Assessment Workflow
"""

import pytest
from workflows.risk_graph import run_assessment, get_decision


class TestWorkflow:
    """Test the complete workflow."""
    
    def test_high_risk_transaction(self):
        """Test that sanctioned country triggers HIGH risk."""
        declaration = {
            "company": "ABC Corp",
            "country": "IR",  # Iran - sanctioned
            "value": 2_000_000
        }
        
        result = run_assessment(declaration)
        decision = get_decision(result)
        
        assert decision["risk_level"] in ["HIGH", "CRITICAL"]
        assert decision["decision"] in ["BLOCK", "FLAG"]
        assert decision["risk_score"] > 0.5
    
    def test_low_risk_transaction(self):
        """Test that normal transaction gets LOW risk."""
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
        """Test that planner correctly identifies required tasks."""
        declaration = {
            "company": "Test Corp",
            "country": "IR",
            "value": 1_500_000
        }
        
        result = run_assessment(declaration)
        
        # Should have sanctions check (country present)
        assert "sanctions_check" in result["tasks"]
        
        # Should have high value review (value > 1M)
        assert "high_value_review" in result["tasks"]
    
    def test_signals_are_generated(self):
        """Test that swarm agents produce signals."""
        declaration = {
            "company": "Test Corp",
            "country": "GB",
            "value": 500_000
        }
        
        result = run_assessment(declaration)
        
        # Should have signals from swarm
        assert len(result["signals"]) > 0
        
        # Each signal should have required fields
        for signal in result["signals"]:
            assert "type" in signal
            assert "score" in signal
    
    def test_explanation_is_generated(self):
        """Test that explanation is generated."""
        declaration = {
            "company": "Test Corp",
            "country": "US",
            "value": 100_000
        }
        
        result = run_assessment(declaration)
        
        assert "explanation" in result
        assert result["explanation"] is not None


class TestSanctions:
    """Test sanctions checking."""
    
    def test_sanctioned_country_detected(self):
        """Test that sanctioned countries are flagged."""
        from mcp.server import call_tool
        
        result = call_tool(
            "check_sanctions",
            caller="test",
            company="Test Corp",
            country="IR"
        )
        
        assert result["country_hit"] == True
        assert result["hit"] == True
    
    def test_clean_country_passes(self):
        """Test that non-sanctioned countries pass."""
        from mcp.server import call_tool
        
        result = call_tool(
            "check_sanctions",
            caller="test",
            company="Test Corp",
            country="US"
        )
        
        assert result["country_hit"] == False


class TestAnomalyDetection:
    """Test anomaly detection."""
    
    def test_high_value_anomaly(self):
        """Test that very high values are flagged as anomalies."""
        from mcp.server import call_tool
        
        result = call_tool(
            "detect_anomalies",
            caller="test",
            value=10_000_000,  # Very high
            country="US",
            company="Test"
        )
        
        assert result["is_anomalous"] == True
        assert result["anomaly_score"] > 0.5
    
    def test_normal_value_passes(self):
        """Test that normal values are not flagged."""
        from mcp.server import call_tool
        
        result = call_tool(
            "detect_anomalies",
            caller="test",
            value=200_000,  # Normal
            country="US",
            company="Test"
        )
        
        assert result["anomaly_score"] < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
