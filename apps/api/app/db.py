from collections.abc import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from pymongo import AsyncMongoClient
from redis.asyncio import Redis
from .config import get_settings

settings = get_settings()
engine = create_async_engine(settings.database_url, pool_pre_ping=True, pool_size=5, max_overflow=10)
Session = async_sessionmaker(engine, expire_on_commit=False)
mongo_client = AsyncMongoClient(settings.mongodb_url, serverSelectionTimeoutMS=4000)
mongo = mongo_client[settings.mongodb_database]
redis = Redis.from_url(settings.redis_url, decode_responses=True, socket_timeout=3)

async def get_db() -> AsyncIterator[AsyncSession]:
    async with Session() as session:
        yield session
