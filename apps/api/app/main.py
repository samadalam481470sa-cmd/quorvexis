import json
import logging
import uuid
from collections import Counter
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter as MetricCounter, generate_latest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from .config import get_settings
from .db import Session, engine, get_db, mongo, mongo_client, redis
from .demo import seed_demo
from .models import Asset, AuditLog, Base, Incident, Membership, Organization, User
from .schemas import AssetCreate, IncidentCreate, IncidentUpdate, Login, Register, SignalIn
from .scoring import score_event
from .security import Current, check_hash, constant_time_equal, issue_token, make_hash, rate_limit, require_role

settings = get_settings()
log = logging.getLogger("quorvexis")
requests_total = MetricCounter("qvx_http_requests_total", "Total HTTP requests", ["method", "status"])

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Development bootstrap; use versioned Alembic migrations for managed production releases.
    if settings.environment == "production":
        log.warning("Production schema migrations must be managed externally.")
    else:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    await mongo.signals.create_index([("org_id", 1), ("ts", -1)])
    await redis.ping()
    yield
    await mongo_client.close()
    await redis.aclose()
    await engine.dispose()

app = FastAPI(title="Quorvexis API", version="0.1.0", lifespan=lifespan, docs_url=None if settings.environment == "production" else "/docs")
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=False,
                   allow_methods=["GET", "POST", "PATCH"], allow_headers=["Authorization", "Content-Type", "X-Request-ID"])
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.hosts)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    request_id = request.headers.get("x-request-id", "")
    if not (0 < len(request_id) <= 64 and request_id.isascii() and request_id.replace("-", "").isalnum()):
        request_id = uuid.uuid4().hex
    if int(request.headers.get("content-length", "0") or 0) > 1024 * 1024:
        return JSONResponse({"detail": "Request too large"}, status_code=413)
    response = await call_next(request)
    for k, v in {
        "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer", "Cache-Control": "no-store",
        "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
        "X-Request-ID": request_id,
    }.items():
        response.headers[k] = v
    requests_total.labels(method=request.method, status=str(response.status_code)).inc()
    return response

def as_json(row):
    return {key: str(value) if isinstance(value, uuid.UUID) else value.isoformat() if isinstance(value, datetime) else value
            for key, value in row.__dict__.items() if not key.startswith("_")}

async def audit(db: AsyncSession, person: Current, action: str, target: str):
    db.add(AuditLog(org_id=person.org_id, actor_id=person.user.id, action=action, target=target))

@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "quorvexis-api"}

@app.get("/readyz")
async def readyz():
    async with engine.connect() as conn:
        await conn.execute(select(1))
    await redis.ping()
    await mongo.command("ping")
    return {"ready": True}

@app.get("/metrics")
async def metrics(request: Request):
    if not settings.metrics_token or not constant_time_equal(
        request.headers.get("x-metrics-token", ""), settings.metrics_token
    ):
        raise HTTPException(404, "Not found")
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/auth/register", status_code=201)
async def register(data: Register, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    await rate_limit(request, "register", limit=5, window=3600)
    email = str(data.email).lower()
    if await db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(409, "Registration unavailable for this email")
    user = User(email=email, password_hash=make_hash(data.password))
    org = Organization(name=data.organization.strip())
    db.add_all([user, org])
    await db.flush()
    db.add(Membership(user_id=user.id, org_id=org.id, role="owner"))
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    return {"access_token": issue_token(user.id, org.id), "token_type": "bearer",
            "user": {"email": user.email, "organization": org.name}}

@app.post("/auth/login")
async def login(data: Login, request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    email = str(data.email).lower()
    await rate_limit(request, "login:" + email, limit=8, window=300)
    user = await db.scalar(select(User).where(User.email == email))
    if not user or not check_hash(user.password_hash, data.password):
        raise HTTPException(401, "Invalid email or password")
    member = await db.scalar(select(Membership).where(Membership.user_id == user.id).order_by(Membership.id))
    if not member:
        raise HTTPException(403, "No active organization membership")
    org = await db.get(Organization, member.org_id)
    return {"access_token": issue_token(user.id, member.org_id), "token_type": "bearer",
            "user": {"email": user.email, "organization": org.name}}

@app.get("/me")
async def me(person: Current, db: Annotated[AsyncSession, Depends(get_db)]):
    org = await db.get(Organization, person.org_id)
    return {"email": person.user.email, "organization": org.name, "organization_id": str(org.id),
            "role": person.member.role, "demo_mode": settings.demo_mode and settings.environment != "production"}

@app.get("/assets")
async def list_assets(person: Current, db: Annotated[AsyncSession, Depends(get_db)]):
    rows = (await db.scalars(select(Asset).where(Asset.org_id == person.org_id).order_by(Asset.created_at.desc()).limit(100))).all()
    return {"items": [as_json(x) for x in rows]}

@app.post("/assets", status_code=201)
async def create_asset(data: AssetCreate, person: Current, db: Annotated[AsyncSession, Depends(get_db)]):
    require_role(person, "analyst")
    row = Asset(org_id=person.org_id, **data.model_dump())
    db.add(row)
    await db.flush()
    await audit(db, person, "asset.created", str(row.id))
    await db.commit()
    return as_json(row)

@app.get("/incidents")
async def list_incidents(person: Current, db: Annotated[AsyncSession, Depends(get_db)]):
    rows = (await db.scalars(select(Incident).where(Incident.org_id == person.org_id).order_by(Incident.created_at.desc()).limit(100))).all()
    return {"items": [as_json(x) for x in rows]}

@app.post("/incidents", status_code=201)
async def create_incident(data: IncidentCreate, person: Current, db: Annotated[AsyncSession, Depends(get_db)]):
    require_role(person, "analyst")
    row = Incident(org_id=person.org_id, **data.model_dump())
    db.add(row)
    await db.flush()
    await audit(db, person, "incident.created", str(row.id))
    await db.commit()
    return as_json(row)

@app.patch("/incidents/{incident_id}")
async def update_incident(incident_id: uuid.UUID, data: IncidentUpdate, person: Current,
                          db: Annotated[AsyncSession, Depends(get_db)]):
    require_role(person, "analyst")
    row = await db.scalar(select(Incident).where(Incident.id == incident_id, Incident.org_id == person.org_id))
    if row is None:
        raise HTTPException(404, "Incident not found")
    row.status = data.status
    await audit(db, person, "incident.updated", str(row.id))
    await db.commit()
    return as_json(row)

@app.get("/signals")
async def get_signals(person: Current):
    cursor = mongo.signals.find({"org_id": str(person.org_id)}, {"_id": 0}).sort("ts", -1).limit(50)
    items = await cursor.to_list(length=50)
    return {"items": [{**e, "ts": e["ts"].isoformat()} for e in items]}

@app.post("/signals", status_code=201)
async def ingest_signal(data: SignalIn, person: Current, db: Annotated[AsyncSession, Depends(get_db)]):
    require_role(person, "analyst")
    if data.asset_id:
        found = await db.scalar(select(Asset.id).where(Asset.id == data.asset_id, Asset.org_id == person.org_id))
        if not found:
            raise HTTPException(404, "Asset not found")
    score = score_event(data.kind, data.severity, data.failed_attempts, data.velocity_kmh)
    event = {"org_id": str(person.org_id), "title": data.title, "kind": data.kind,
             "score": score.score, "band": score.band, "reasons": list(score.reasons),
             "asset_id": str(data.asset_id) if data.asset_id else None,
             "synthetic": False, "ts": datetime.now(timezone.utc)}
    await mongo.signals.insert_one(event)
    await audit(db, person, "signal.ingested", data.kind)
    await db.commit()
    return {"score": score.score, "band": score.band, "reasons": score.reasons}

@app.post("/demo/seed")
async def seed(person: Current, db: Annotated[AsyncSession, Depends(get_db)]):
    if not settings.demo_mode or settings.environment == "production":
        raise HTTPException(404, "Not found")
    require_role(person, "owner")
    created = await seed_demo(db, person.org_id)
    await audit(db, person, "demo.seeded", "synthetic")
    await db.commit()
    return {"seeded": created, "synthetic": True}

@app.get("/overview")
async def overview(person: Current, db: Annotated[AsyncSession, Depends(get_db)]):
    asset_count = await db.scalar(select(func.count()).select_from(Asset).where(Asset.org_id == person.org_id))
    open_count = await db.scalar(select(func.count()).select_from(Incident).where(
        Incident.org_id == person.org_id, Incident.status != "resolved"))
    critical_count = await db.scalar(select(func.count()).select_from(Incident).where(
        Incident.org_id == person.org_id, Incident.severity == "critical", Incident.status != "resolved"))
    start = datetime.now(timezone.utc) - timedelta(days=7)
    pipeline = [
        {"$match": {"org_id": str(person.org_id), "ts": {"$gte": start}}},
        {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$ts"}},
                    "count": {"$sum": 1}, "avg_risk": {"$avg": "$score"}}},
        {"$sort": {"_id": 1}}
    ]
    days = await mongo.signals.aggregate(pipeline).to_list(length=8)
    buckets = {x["_id"]: x for x in days}
    today = datetime.now(timezone.utc).date()
    trend = [{"day": (today - timedelta(days=6 - i)).strftime("%a"),
              "date": (today - timedelta(days=6 - i)).isoformat(),
              "count": buckets.get((today - timedelta(days=6 - i)).isoformat(), {}).get("count", 0),
              "risk": round(buckets.get((today - timedelta(days=6 - i)).isoformat(), {}).get("avg_risk", 0))}
             for i in range(7)]
    signals_24h = await mongo.signals.count_documents({
        "org_id": str(person.org_id), "ts": {"$gte": datetime.now(timezone.utc) - timedelta(hours=24)}
    })
    return {"assets": asset_count, "open_incidents": open_count, "critical_incidents": critical_count,
            "signals_24h": signals_24h, "trend": trend,
            "synthetic_demo": settings.demo_mode and settings.environment != "production"}
