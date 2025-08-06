import pickle
import hashlib
from .redis_config import get_redis
from fastapi import Request


def generate_cache_key(request: Request):
    request_data = request.query_params
    router = request.scope['router']

    hashed_data = pickle.dumps(sorted(request_data.items()))
    digest = hashlib.sha256(hashed_data).hexdigest()
    return f"cache:{router}:{digest}"


async def delete_caches(pattern: str):
    """Delete all caches containing a specified pattern"""
    async with get_redis() as redis:
        keys = await redis.keys(pattern)
        if keys:
            await redis.delete(*keys)


async def set_cache(key: str, data):
    async with get_redis() as redis:
        hashed = pickle.dumps(data)
        await redis.set(key, hashed)


async def get_cache(key: str):
    async with get_redis() as redis:
        data = await redis.get(key)
        try:
            data = pickle.loads(data)
            return data
        except TypeError:
            return None