from functools import lru_cache
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+asyncpg://qvx:qvx@localhost:5432/qvx"
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "quorvexis"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = Field(min_length=32)
    jwt_issuer: str = "quorvexis-api"
    jwt_audience: str = "quorvexis-web"
    cors_origins: str = "http://localhost:3000"
    allowed_hosts: str = "localhost,127.0.0.1,api"
    demo_mode: bool = False
    metrics_token: str = ""

    @field_validator("jwt_secret")
    @classmethod
    def reject_placeholder(cls, value: str) -> str:
        if value.lower().startswith(("change-me", "replace-me", "your-secret")):
            raise ValueError("JWT_SECRET must be generated using a cryptographically random value")
        return value

    @property
    def origins(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

    @property
    def hosts(self) -> list[str]:
        return [x.strip() for x in self.allowed_hosts.split(",") if x.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()
