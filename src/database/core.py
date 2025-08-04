from contextlib import asynccontextmanager
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass
import os


load_dotenv()

DATABASE_URL = os.getenv("DB_URL")

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True
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