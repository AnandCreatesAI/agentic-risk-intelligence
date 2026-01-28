# mcp/tools.py
# MCP (Tool Isolation Layer)
# Agents NEVER access external systems directly - all access goes through these tools.
# This provides security, governance, logging, and safe scaling.

from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib

# ============================================================================
# MOCK DATA (In production, these would be external API calls or DB queries)
# ============================================================================

# OFAC-style sanctions list
SANCTIONS_DATABASE = {
    "companies": {
        "EVIL CORP": {"listed": True, "source": "OFAC", "date": "2023-01-15"},
        "SHADOW TRADING LLC": {"listed": True, "source": "OFAC", "date": "2022-08-20"},
        "FRONT COMPANY INC": {"listed": True, "source": "EU", "date": "2023-06-01"},
    },
    "countries": {
        "IR": {"sanctioned": True, "level": "comprehensive", "source": "OFAC"},
        "KP": {"sanctioned": True, "level": "comprehensive", "source": "OFAC"},
        "SY": {"sanctioned": True, "level": "comprehensive", "source": "OFAC"},
        "CU": {"sanctioned": True, "level": "partial", "source": "OFAC"},
        "RU": {"sanctioned": True, "level": "sectoral", "source": "OFAC"},
    }
}

# Historical transactions for similarity matching
HISTORICAL_RISKY_CASES = [
    {"company": "ACME EXPORTS", "country": "IR", "value": 1500000, "outcome": "blocked", "risk_score": 0.95},
    {"company": "GLOBAL TRADE CO", "country": "SY", "value": 800000, "outcome": "blocked", "risk_score": 0.88},
    {"company": "TECH IMPORTS LTD", "country": "RU", "value": 2500000, "outcome": "flagged", "risk_score": 0.72},
    {"company": "COMMODITY DEALERS", "country": "CU", "value": 500000, "outcome": "blocked", "risk_score": 0.85},
]

# Normal transaction patterns (for anomaly detection)
NORMAL_PATTERNS = {
    "avg_transaction_value": 250000,
    "std_transaction_value": 150000,
    "common_countries": ["US", "GB", "DE", "FR", "JP", "CA", "AU"],
    "typical_frequency": "weekly"
}


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

def check_sanctions(company: str, country: Optional[str] = None) -> Dict[str, Any]:
    """
    Check if a company or country is on sanctions lists.
    Returns structured result with source and evidence.
    """
    result = {
        "timestamp": datetime.now().isoformat(),
        "tool": "sanctions_check",
        "company_checked": company,
        "country_checked": country,
        "company_hit": False,
        "country_hit": False,
        "sources": [],
        "risk_indicators": []
    }
    
    # Check company against sanctions list (case-insensitive, partial match)
    company_upper = company.upper()
    for sanctioned_company, details in SANCTIONS_DATABASE["companies"].items():
        if sanctioned_company in company_upper or company_upper in sanctioned_company:
            result["company_hit"] = True
            result["sources"].append({
                "type": "company_sanction",
                "name": sanctioned_company,
                "source": details["source"],
                "date": details["date"]
            })
            result["risk_indicators"].append(f"Company matches sanctioned entity: {sanctioned_company}")
    
    # Check country
    if country and country.upper() in SANCTIONS_DATABASE["countries"]:
        country_info = SANCTIONS_DATABASE["countries"][country.upper()]
        result["country_hit"] = True
        result["sources"].append({
            "type": "country_sanction",
            "country": country.upper(),
            "level": country_info["level"],
            "source": country_info["source"]
        })
        result["risk_indicators"].append(f"Country {country} under {country_info['level']} sanctions")
    
    # Calculate hit score
    result["hit"] = result["company_hit"] or result["country_hit"]
    result["severity"] = "HIGH" if result["company_hit"] else ("MEDIUM" if result["country_hit"] else "NONE")
    
    return result


def search_similar_cases(company: str, country: str, value: float) -> Dict[str, Any]:
    """
    Search for similar historical cases using vector similarity (mocked).
    In production, this would query a vector database.
    """
    similar_cases = []
    
    for case in HISTORICAL_RISKY_CASES:
        similarity_score = 0.0
        
        # Country match is heavily weighted
        if case["country"] == country:
            similarity_score += 0.5
        
        # Value similarity (within 50% range)
        value_ratio = min(value, case["value"]) / max(value, case["value"])
        if value_ratio > 0.5:
            similarity_score += 0.3 * value_ratio
        
        # Company name similarity (simple check)
        if any(word in company.upper() for word in case["company"].upper().split()):
            similarity_score += 0.2
        
        if similarity_score > 0.3:
            similar_cases.append({
                "case": case,
                "similarity": round(similarity_score, 2)
            })
    
    # Sort by similarity
    similar_cases.sort(key=lambda x: x["similarity"], reverse=True)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "tool": "similarity_search",
        "query": {"company": company, "country": country, "value": value},
        "matches": similar_cases[:5],  # Top 5 matches
        "highest_similarity": similar_cases[0]["similarity"] if similar_cases else 0.0
    }


def detect_anomalies(value: float, country: str, company: str) -> Dict[str, Any]:
    """
    Detect statistical anomalies in the transaction.
    """
    anomalies = []
    anomaly_score = 0.0
    
    # Value anomaly (Z-score based)
    z_score = (value - NORMAL_PATTERNS["avg_transaction_value"]) / NORMAL_PATTERNS["std_transaction_value"]
    if abs(z_score) > 2:
        anomalies.append({
            "type": "value_anomaly",
            "description": f"Transaction value {value:,.0f} is {z_score:.1f} std devs from mean",
            "severity": "HIGH" if abs(z_score) > 3 else "MEDIUM"
        })
        anomaly_score += min(abs(z_score) / 5, 0.4)
    
    # Country anomaly
    if country not in NORMAL_PATTERNS["common_countries"]:
        anomalies.append({
            "type": "country_anomaly",
            "description": f"Country {country} is not in typical trading partners",
            "severity": "MEDIUM"
        })
        anomaly_score += 0.3
    
    # High value threshold
    if value > 1_000_000:
        anomalies.append({
            "type": "high_value",
            "description": f"Transaction exceeds high-value threshold of 1M",
            "severity": "MEDIUM"
        })
        anomaly_score += 0.2
    
    return {
        "timestamp": datetime.now().isoformat(),
        "tool": "anomaly_detection",
        "input": {"value": value, "country": country, "company": company},
        "anomalies": anomalies,
        "anomaly_score": round(min(anomaly_score, 1.0), 2),
        "is_anomalous": anomaly_score > 0.3
    }


def check_patterns(company: str, country: str, value: float) -> Dict[str, Any]:
    """
    Check for known risky patterns (structuring, layering, etc.)
    """
    patterns_found = []
    pattern_score = 0.0
    
    # Round number check (potential structuring)
    if value % 100000 == 0 and value > 500000:
        patterns_found.append({
            "type": "round_number",
            "description": "Large round transaction amount may indicate structuring",
            "severity": "LOW"
        })
        pattern_score += 0.15
    
    # Just-under threshold (common evasion tactic)
    thresholds = [1000000, 500000, 10000]
    for threshold in thresholds:
        if threshold * 0.95 <= value < threshold:
            patterns_found.append({
                "type": "threshold_proximity",
                "description": f"Value is just under {threshold:,} threshold",
                "severity": "MEDIUM"
            })
            pattern_score += 0.25
    
    # High-risk corridor
    high_risk_corridors = [("US", "IR"), ("US", "RU"), ("EU", "SY")]
    # Simplified check
    if country in ["IR", "RU", "SY", "KP"]:
        patterns_found.append({
            "type": "high_risk_corridor",
            "description": f"Transaction involves high-risk jurisdiction: {country}",
            "severity": "HIGH"
        })
        pattern_score += 0.4
    
    return {
        "timestamp": datetime.now().isoformat(),
        "tool": "pattern_detection",
        "patterns": patterns_found,
        "pattern_score": round(min(pattern_score, 1.0), 2)
    }


def get_company_info(company: str) -> Dict[str, Any]:
    """
    Get company information from external registries (mocked).
    """
    # Mock company database
    companies = {
        "ABC CORP": {
            "registered": True,
            "jurisdiction": "US",
            "years_active": 15,
            "industry": "manufacturing",
            "risk_rating": "low"
        }
    }
    
    company_upper = company.upper()
    if company_upper in companies:
        return {
            "found": True,
            "info": companies[company_upper],
            "timestamp": datetime.now().isoformat()
        }
    
    # Unknown company - slight risk
    return {
        "found": False,
        "info": None,
        "risk_note": "Company not found in registry - manual verification recommended",
        "timestamp": datetime.now().isoformat()
    }
