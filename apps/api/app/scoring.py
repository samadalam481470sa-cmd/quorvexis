"""Explainable deterministic event scoring; not a trained ML model."""
from dataclasses import dataclass

WEIGHTS = {
    "auth_failure": 9,
    "network_anomaly": 13,
    "configuration_drift": 7,
    "malware_indicator": 24,
    "policy_violation": 11,
}

@dataclass(frozen=True)
class RiskResult:
    score: int
    band: str
    reasons: tuple[str, ...]

def score_event(kind: str, severity: int, failed_attempts: int = 0, velocity_kmh: float = 0) -> RiskResult:
    if kind not in WEIGHTS or not 0 <= severity <= 100 or failed_attempts < 0 or velocity_kmh < 0:
        raise ValueError("Invalid signal")
    score = round(severity * 0.65) + WEIGHTS[kind]
    reasons = [f"Source severity contributes {round(severity * 0.65)} points", f"{kind.replace('_', ' ')} category adds {WEIGHTS[kind]}"]
    if failed_attempts >= 10:
        score += min(18, failed_attempts // 5)
        reasons.append("Repeated authentication attempts")
    if velocity_kmh > 900:
        score += 20
        reasons.append("Unusual geographic velocity")
    score = max(0, min(100, score))
    band = "critical" if score >= 85 else "high" if score >= 65 else "medium" if score >= 35 else "low"
    return RiskResult(score, band, tuple(reasons))
