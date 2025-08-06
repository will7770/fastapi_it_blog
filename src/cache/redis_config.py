from typing import AsyncGenerator, AsyncIterator
from dotenv import load_dotenv
from redis.asyncio import Redis, ConnectionPool
import os
from contextlib import asynccontextmanager


load_dotenv()
url = os.getenv("REDIS_URL")

pool = ConnectionPool.from_url(
    url=url,
    db=0,
    max_connections=10,
    decode_responses=False,
    socket_connect_timeout=5,
    socket_keepalive=True
)
r = Redis(connection_pool=pool)

@asynccontextmanager
async def get_redis() -> AsyncIterator[Redis]:
    try:
        yield r
    finally:
        await r.aclose()