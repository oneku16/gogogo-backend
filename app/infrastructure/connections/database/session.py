from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool, QueuePool
import os

from app.configurations.database import postgres_settings

# Determine Pool Class based on App Context (App vs Worker)
# Celery Workers using asyncio.run() MUST use NullPool because connections are tied to the event loop.
pool_class_name = os.getenv("DB_POOL_CLASS", "QueuePool")
pool_class = NullPool if pool_class_name == "NullPool" else None # None defaults to QueuePool in create_async_engine

engine = create_async_engine(
    postgres_settings.dsn,
    echo=False,
    future=True,
    poolclass=pool_class,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
