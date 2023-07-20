from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.conf.config import settings

# URL = f'postgresql+asyncpg://{user}:{password}@{host}:{port}/{db_name}?async_fallback=True'
URL = settings.sqlalchemy_database_url

engine = create_async_engine(URL, echo=True)
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        yield session
