"""Explicit opt-in, synthetic-only data for local showcase environments."""
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Asset, Incident
from .db import mongo

ASSETS = [
    ("edge-gateway-prod", "aws", "us-east-1", "network", 82),
    ("identity-control-plane", "azure", "eastus", "identity", 61),
    ("quorvexis-postgres-01", "aws", "us-east-1", "database", 26),
    ("inference-cluster-a", "gcp", "us-central1", "compute", 42),
    ("customer-api-mesh", "aws", "us-west-2", "container", 18),
    ("onprem-auth-relay", "on-prem", "us-dallas", "network", 73),
]
INCIDENTS = [
    ("Anomalous cross-region sign-in burst", "critical", "investigating", "identity-control-plane"),
    ("Publicly exposed security group", "high", "open", "edge-gateway-prod"),
    ("Container image drift detected", "medium", "open", "customer-api-mesh"),
    ("Credential stuffing attempt blocked", "high", "resolved", "onprem-auth-relay"),
]

async def seed_demo(db: AsyncSession, org_id) -> bool:
    found = await db.scalar(select(Asset.id).where(Asset.org_id == org_id).limit(1))
    if found:
        return False
    db.add_all([Asset(org_id=org_id, name=name, provider=provider, region=region, kind=kind, risk=risk)
                for name, provider, region, kind, risk in ASSETS])
    db.add_all([Incident(org_id=org_id, title=title, severity=sev, status=status, source=source)
                for title, sev, status, source in INCIDENTS])
    await db.commit()
    now = datetime.now(timezone.utc)
    events = []
    kinds = ["auth_failure", "network_anomaly", "configuration_drift", "policy_violation", "malware_indicator"]
    for i in range(70):
        score = min(100, 14 + (i * 17) % 83)
        events.append({
            "org_id": str(org_id), "title": f"Synthetic {kinds[i % 5].replace('_', ' ')} event",
            "kind": kinds[i % 5], "score": score,
            "band": "critical" if score >= 85 else "high" if score >= 65 else "medium" if score >= 35 else "low",
            "reasons": ["Synthetic demonstration event"], "synthetic": True,
            "ts": now - timedelta(hours=i * 2 + (i % 4))
        })
    await mongo.signals.insert_many(events)
    return True
