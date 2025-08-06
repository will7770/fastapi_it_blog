from contextlib import asynccontextmanager
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Table, MetaData, insert, select
import os
from src.utils import hash_password


load_dotenv()

SUPERUSER_NAME=os.getenv("SUPERUSER_NAME")
SUPERUSER_PASSWORD=os.getenv("SUPERUSER_PASSWORD")
SUPERUSER_EMAIL=os.getenv("SUPERUSER_EMAIL")

DATABASE_URL = os.getenv("DB_URL")

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
)

sessions = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

@asynccontextmanager
async def get_db():
    async with sessions() as session:
        yield session

async def get_session():
    async with sessions() as session:
        try:
            yield session
        finally:
            await session.close()



class Base(DeclarativeBase):
    pass


async def init_db():
    async with engine.begin() as con:
        await con.run_sync(Base.metadata.create_all)


async def create_first_superuser():
    from src.database.models.users import User, Roles
    async with get_db() as session:
        stmt = (await session.execute(select(User).where(User.username==SUPERUSER_NAME))).scalar_one_or_none()
        if not stmt:
            hashed_password = hash_password(SUPERUSER_PASSWORD)
            superuser = User(
                username=SUPERUSER_NAME,
                password=hashed_password,
                email=SUPERUSER_EMAIL,
                role=Roles.ADMIN
            )
            session.add(superuser)
            await session.commit()
