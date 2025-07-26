from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass



DATABASE_URL = "postgresql+asyncpg://blog_admin:1029384756@localhost:5432/fastapi_blog"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True
)

sessions = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

async def get_session():
    async with sessions() as session:
        yield session



class Base(DeclarativeBase):
    pass


async def init_db():
    async with engine.begin() as con:
        await con.run_sync(Base.metadata.create_all)