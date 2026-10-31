from typing import Dict, Any, Optional, List
from datetime import datetime

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

HISTORICAL_RISKY_CASES = [
    {"company": "ACME EXPORTS", "country": "IR", "value": 1500000, "outcome": "blocked", "risk_score": 0.95},
    {"company": "GLOBAL TRADE CO", "country": "SY", "value": 800000, "outcome": "blocked", "risk_score": 0.88},
    {"company": "TECH IMPORTS LTD", "country": "RU", "value": 2500000, "outcome": "flagged", "risk_score": 0.72},
    {"company": "COMMODITY DEALERS", "country": "CU", "value": 500000, "outcome": "blocked", "risk_score": 0.85},
]

NORMAL_PATTERNS = {
    "avg_transaction_value": 250000,
    "std_transaction_value": 150000,
    "common_countries": ["US", "GB", "DE", "FR", "JP", "CA", "AU"],
}


def check_sanctions(company: str, country: Optional[str] = None) -> Dict[str, Any]:
    result = {
        "timestamp": datetime.now().isoformat(),
        "company_checked": company,
        "country_checked": country,
        "company_hit": False,
        "country_hit": False,
        "sources": [],
        "risk_indicators": []
    }

    company_upper = (company or "").upper()

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

    if country and country.upper() in SANCTIONS_DATABASE["countries"]:
        info = SANCTIONS_DATABASE["countries"][country.upper()]
        result["country_hit"] = True
        result["sources"].append({
            "type": "country_sanction",
            "country": country.upper(),
            "level": info["level"],
            "source": info["source"]
        })
        result["risk_indicators"].append(f"Country {country} under {info['level']} sanctions")

    result["hit"] = result["company_hit"] or result["country_hit"]
    result["severity"] = "HIGH" if result["company_hit"] else (
        "MEDIUM" if result["country_hit"] else "NONE"
    )

    return result


def search_similar_cases(company: str, country: str, value: float) -> Dict[str, Any]:
    similar_cases: List[Dict[str, Any]] = []

    for case in HISTORICAL_RISKY_CASES:
        similarity = 0.0

        if case["country"] == country:
            similarity += 0.5

        if value and case["value"]:
            ratio = min(value, case["value"]) / max(value, case["value"])
            if ratio > 0.5:
                similarity += 0.3 * ratio

        if company and any(word in company.upper() for word in case["company"].split()):
            similarity += 0.2

        if similarity > 0.3:
            similar_cases.append({
                "case": case,
                "similarity": round(similarity, 2)
            })

    similar_cases.sort(key=lambda x: x["similarity"], reverse=True)

    return {
        "timestamp": datetime.now().isoformat(),
        "matches": similar_cases[:5],
        "highest_similarity": similar_cases[0]["similarity"] if similar_cases else 0.0
    }


def detect_anomalies(value: float, country: str, company: str) -> Dict[str, Any]:
    anomalies = []
    anomaly_score = 0.0

    z_score = (value - NORMAL_PATTERNS["avg_transaction_value"]) / NORMAL_PATTERNS["std_transaction_value"]

    if abs(z_score) > 2:
        anomalies.append({
            "type": "value_anomaly",
            "description": f"Value {value} is {z_score:.1f} std dev from mean",
            "severity": "HIGH" if abs(z_score) > 3 else "MEDIUM"
        })
        anomaly_score += min(abs(z_score) / 5, 0.4)

    if country not in NORMAL_PATTERNS["common_countries"]:
        anomalies.append({
            "type": "country_anomaly",
            "description": f"{country} not typical trading partner",
            "severity": "MEDIUM"
        })
        anomaly_score += 0.3

    if value > 1_000_000:
        anomalies.append({
            "type": "high_value",
            "description": "High transaction value",
            "severity": "MEDIUM"
        })
        anomaly_score += 0.2

    anomaly_score = min(anomaly_score, 1.0)

    return {
        "timestamp": datetime.now().isoformat(),
        "anomalies": anomalies,
        "anomaly_score": round(anomaly_score, 2),
        "is_anomalous": anomaly_score > 0.3
    }


def check_patterns(company: str, country: str, value: float) -> Dict[str, Any]:
    patterns = []
    pattern_score = 0.0

    if value and value % 100000 == 0 and value > 500000:
        patterns.append({
            "type": "round_number",
            "description": "Large round amount",
            "severity": "LOW"
        })
        pattern_score += 0.15

    thresholds = [1_000_000, 500_000, 10_000]

    for threshold in thresholds:
        if threshold * 0.95 <= value < threshold:
            patterns.append({
                "type": "threshold_proximity",
                "description": f"Value just under {threshold}",
                "severity": "MEDIUM"
            })
            pattern_score += 0.25

    if country in ["IR", "RU", "SY", "KP"]:
        patterns.append({
            "type": "high_risk_corridor",
            "description": f"High-risk jurisdiction {country}",
            "severity": "HIGH"
        })
        pattern_score += 0.4

    pattern_score = min(pattern_score, 1.0)

    return {
        "timestamp": datetime.now().isoformat(),
        "patterns": patterns,
        "pattern_score": round(pattern_score, 2)
    }


def get_company_info(company: str) -> Dict[str, Any]:
    companies = {
        "ABC CORP": {
            "registered": True,
            "jurisdiction": "US",
            "years_active": 15,
            "industry": "manufacturing",
            "risk_rating": "low"
        }
    }

    company_upper = (company or "").upper()

    if company_upper in companies:
        return {
            "found": True,
            "info": companies[company_upper],
            "timestamp": datetime.now().isoformat()
        }

    return {
        "found": False,
        "info": None,
        "risk_note": "Company not found - manual verification recommended",
        "timestamp": datetime.now().isoformat()
    }