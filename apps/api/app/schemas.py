from typing import Literal
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator

class Register(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    organization: str = Field(min_length=2, max_length=120)

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if not (any(ch.islower() for ch in value) and any(ch.isupper() for ch in value) and any(ch.isdigit() for ch in value)):
            raise ValueError("Use uppercase, lowercase, and a number")
        return value

class Login(BaseModel):
    email: EmailStr
    password: str

class AssetCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    provider: Literal["aws", "azure", "gcp", "on-prem"]
    region: str = Field(min_length=2, max_length=50)
    kind: Literal["compute", "database", "network", "container", "identity"]
    risk: int = Field(ge=0, le=100, default=0)

class IncidentCreate(BaseModel):
    title: str = Field(min_length=4, max_length=180)
    severity: Literal["critical", "high", "medium", "low"]
    source: str = Field(max_length=100, default="manual")

class IncidentUpdate(BaseModel):
    status: Literal["open", "investigating", "resolved"]

class SignalIn(BaseModel):
    title: str = Field(min_length=4, max_length=200)
    kind: Literal["auth_failure", "network_anomaly", "configuration_drift", "malware_indicator", "policy_violation"]
    severity: int = Field(ge=0, le=100)
    failed_attempts: int = Field(ge=0, le=10000, default=0)
    velocity_kmh: float = Field(ge=0, le=50000, default=0)
    asset_id: UUID | None = None
