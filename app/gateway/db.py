from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from redis.asyncio import Redis

from app.gateway.config import settings

# Postgres
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Cache (Redis)
cache: Redis = Redis.from_url(settings.CACHE_URL, decode_responses=True)
