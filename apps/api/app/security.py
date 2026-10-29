import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .config import get_settings
from .db import get_db, redis
from .models import Membership, User

settings = get_settings()
hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
ROLES = {"viewer": 0, "analyst": 1, "admin": 2, "owner": 3}

def make_hash(password: str) -> str:
    return hasher.hash(password)

def check_hash(encoded: str, password: str) -> bool:
    try:
        return hasher.verify(encoded, password)
    except (VerifyMismatchError, InvalidHashError):
        return False

def issue_token(user_id: uuid.UUID, org_id: uuid.UUID) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user_id), "org": str(org_id), "iss": settings.jwt_issuer,
         "aud": settings.jwt_audience, "iat": now, "exp": now + timedelta(minutes=15), "jti": uuid.uuid4().hex},
        settings.jwt_secret, algorithm="HS256"
    )

async def rate_limit(request: Request, identity: str, limit: int = 8, window: int = 300) -> None:
    # Key contains only a digest; do not trust X-Forwarded-For from arbitrary clients.
    ip = request.client.host if request.client else "unknown"
    key = "rl:" + hashlib.sha256(f"{ip}:{identity}".encode()).hexdigest()
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, window)
    if count > limit:
        raise HTTPException(status_code=429, detail="Too many attempts. Try again later.")

class Principal:
    def __init__(self, user: User, membership: Membership):
        self.user = user
        self.member = membership
        self.org_id = membership.org_id

async def principal(request: Request, db: Annotated[AsyncSession, Depends(get_db)]) -> Principal:
    header = request.headers.get("authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = jwt.decode(header[7:], settings.jwt_secret, algorithms=["HS256"],
                             audience=settings.jwt_audience, issuer=settings.jwt_issuer,
                             options={"require": ["sub", "org", "exp", "iat", "jti"]})
        user_id, org_id = uuid.UUID(payload["sub"]), uuid.UUID(payload["org"])
    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        raise HTTPException(status_code=401, detail="Invalid or expired session") from None
    result = await db.execute(select(User, Membership).join(
        Membership, Membership.user_id == User.id
    ).where(User.id == user_id, Membership.org_id == org_id))
    found = result.first()
    if not found:
        raise HTTPException(status_code=401, detail="Session no longer authorized")
    return Principal(found[0], found[1])

Current = Annotated[Principal, Depends(principal)]

def require_role(person: Principal, minimum: str) -> None:
    if ROLES.get(person.member.role, -1) < ROLES[minimum]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

def constant_time_equal(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())
