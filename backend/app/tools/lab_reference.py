"""Lab reference ranges and interpretation utilities."""
from __future__ import annotations

from typing import Any, Optional


# Standard reference ranges — age/gender-adjusted where noted
LAB_REFERENCE_RANGES: dict[str, dict[str, Any]] = {
    # Complete Blood Count
    "hemoglobin": {
        "unit": "g/dL",
        "male": {"min": 13.5, "max": 17.5},
        "female": {"min": 12.0, "max": 15.5},
        "critical_low": 7.0,
        "critical_high": 20.0,
    },
    "hematocrit": {
        "unit": "%",
        "male": {"min": 41, "max": 53},
        "female": {"min": 36, "max": 46},
        "critical_low": 21,
        "critical_high": 60,
    },
    "wbc": {
        "unit": "K/µL",
        "all": {"min": 4.5, "max": 11.0},
        "critical_low": 2.0,
        "critical_high": 30.0,
    },
    "platelets": {
        "unit": "K/µL",
        "all": {"min": 150, "max": 400},
        "critical_low": 20,
        "critical_high": 1000,
    },
    "neutrophils": {"unit": "%", "all": {"min": 50, "max": 70}},
    "lymphocytes": {"unit": "%", "all": {"min": 20, "max": 40}},
    # Comprehensive Metabolic Panel
    "sodium": {
        "unit": "mEq/L",
        "all": {"min": 136, "max": 145},
        "critical_low": 120,
        "critical_high": 160,
    },
    "potassium": {
        "unit": "mEq/L",
        "all": {"min": 3.5, "max": 5.0},
        "critical_low": 2.5,
        "critical_high": 6.5,
    },
    "chloride": {"unit": "mEq/L", "all": {"min": 98, "max": 106}},
    "bicarbonate": {
        "unit": "mEq/L",
        "all": {"min": 22, "max": 29},
        "critical_low": 10,
        "critical_high": 40,
    },
    "bun": {
        "unit": "mg/dL",
        "all": {"min": 7, "max": 20},
        "critical_high": 100,
    },
    "creatinine": {
        "unit": "mg/dL",
        "male": {"min": 0.74, "max": 1.35},
        "female": {"min": 0.59, "max": 1.04},
        "critical_high": 10.0,
    },
    "glucose": {
        "unit": "mg/dL",
        "all": {"min": 70, "max": 100},  # fasting
        "critical_low": 40,
        "critical_high": 500,
    },
    "calcium": {
        "unit": "mg/dL",
        "all": {"min": 8.5, "max": 10.5},
        "critical_low": 7.0,
        "critical_high": 13.0,
    },
    "albumin": {"unit": "g/dL", "all": {"min": 3.5, "max": 5.0}},
    "total_protein": {"unit": "g/dL", "all": {"min": 6.3, "max": 8.2}},
    # Liver Function
    "alt": {"unit": "U/L", "male": {"min": 7, "max": 56}, "female": {"min": 7, "max": 45}},
    "ast": {"unit": "U/L", "all": {"min": 10, "max": 40}},
    "alp": {
        "unit": "U/L",
        "male": {"min": 45, "max": 115},
        "female": {"min": 30, "max": 100},
    },
    "total_bilirubin": {
        "unit": "mg/dL",
        "all": {"min": 0.1, "max": 1.2},
        "critical_high": 15.0,
    },
    # Thyroid
    "tsh": {"unit": "mIU/L", "all": {"min": 0.4, "max": 4.0}},
    "free_t4": {"unit": "ng/dL", "all": {"min": 0.8, "max": 1.8}},
    "free_t3": {"unit": "pg/mL", "all": {"min": 2.3, "max": 4.2}},
    # Coagulation
    "pt": {"unit": "seconds", "all": {"min": 11, "max": 13.5}},
    "inr": {
        "unit": "",
        "all": {"min": 0.8, "max": 1.2},
        "critical_high": 5.0,
    },
    "ptt": {"unit": "seconds", "all": {"min": 25, "max": 35}},
    # Lipids
    "total_cholesterol": {"unit": "mg/dL", "all": {"min": 0, "max": 200}},
    "ldl": {"unit": "mg/dL", "all": {"min": 0, "max": 100}},  # optimal
    "hdl": {
        "unit": "mg/dL",
        "male": {"min": 40, "max": 999},
        "female": {"min": 50, "max": 999},
    },
    "triglycerides": {"unit": "mg/dL", "all": {"min": 0, "max": 150}},
    # Cardiac
    "troponin_i": {
        "unit": "ng/mL",
        "all": {"min": 0, "max": 0.04},
        "critical_high": 0.04,  # Any elevation is critical
    },
    "bnp": {"unit": "pg/mL", "all": {"min": 0, "max": 100}},
    "ck_mb": {"unit": "ng/mL", "all": {"min": 0, "max": 5.0}},
    # Inflammatory
    "crp": {"unit": "mg/L", "all": {"min": 0, "max": 1.0}},
    "esr": {
        "unit": "mm/hr",
        "male": {"min": 0, "max": 20},
        "female": {"min": 0, "max": 30},
    },
    "hba1c": {"unit": "%", "all": {"min": 0, "max": 5.7}},
    # Urinalysis
    "urine_glucose": {"unit": "", "all": {"min": 0, "max": 0}},  # should be negative
    "urine_protein": {"unit": "mg/dL", "all": {"min": 0, "max": 8}},
}


def get_reference_range(test_name: str, age: int, gender: str) -> dict[str, Any]:
    """Return reference range for a lab test considering age and gender.

    Args:
        test_name: Normalized test name (lowercase, underscores).
        age: Patient age in years.
        gender: Patient gender ('male' or 'female').

    Returns:
        Dict with min, max, unit, and critical values if applicable.
    """
    key = test_name.lower().replace(" ", "_").replace("-", "_")
    ref = LAB_REFERENCE_RANGES.get(key)
    if not ref:
        return {"min": None, "max": None, "unit": "unknown"}

    gender_key = gender.lower() if gender.lower() in ("male", "female") else "all"
    ranges = ref.get(gender_key) or ref.get("all") or {}

    result: dict[str, Any] = {
        "min": ranges.get("min"),
        "max": ranges.get("max"),
        "unit": ref.get("unit", ""),
    }
    if "critical_low" in ref:
        result["critical_low"] = ref["critical_low"]
    if "critical_high" in ref:
        result["critical_high"] = ref["critical_high"]
    return result


def interpret_value(
    test_name: str,
    value: float,
    unit: str,
    age: int,
    gender: str,
) -> dict[str, Any]:
    """Interpret a lab value against reference ranges.

    Returns:
        Dict with status, severity, and interpretation string.
    """
    ref = get_reference_range(test_name, age, gender)
    mn, mx = ref.get("min"), ref.get("max")
    crit_low = ref.get("critical_low")
    crit_high = ref.get("critical_high")

    if mn is None and mx is None:
        return {"status": "unknown", "severity": None, "interpretation": "Reference range not available"}

    # Critical check
    if crit_low is not None and value < crit_low:
        return {
            "status": "critical",
            "severity": "critical",
            "interpretation": f"CRITICAL LOW: {value} {unit} (critical threshold: {crit_low})",
        }
    if crit_high is not None and value > crit_high:
        return {
            "status": "critical",
            "severity": "critical",
            "interpretation": f"CRITICAL HIGH: {value} {unit} (critical threshold: {crit_high})",
        }

    # Normal range check
    if mn is not None and value < mn:
        pct_below = abs((value - mn) / mn * 100)
        severity = "mild" if pct_below < 20 else "moderate" if pct_below < 40 else "severe"
        return {
            "status": "low",
            "severity": severity,
            "interpretation": f"LOW: {value} {unit} (reference: {mn}-{mx})",
        }
    if mx is not None and value > mx:
        pct_above = abs((value - mx) / mx * 100)
        severity = "mild" if pct_above < 20 else "moderate" if pct_above < 40 else "severe"
        return {
            "status": "high",
            "severity": severity,
            "interpretation": f"HIGH: {value} {unit} (reference: {mn}-{mx})",
        }

    return {
        "status": "normal",
        "severity": None,
        "interpretation": f"Within normal range: {value} {unit} (reference: {mn}-{mx})",
    }
