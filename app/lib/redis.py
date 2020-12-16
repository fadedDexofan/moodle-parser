import contextlib

import aioredis
import redis

from app.settings.config import settings


@contextlib.contextmanager
def redis_sync_client() -> redis.Redis:
    client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD,
        db=1,
    )
    try:
        yield client
    finally:
        client.close()


@contextlib.asynccontextmanager
async def redis_async_client() -> aioredis.Redis:
    client = await aioredis.create_redis(
        f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}',
        password=settings.REDIS_PASSWORD,
        db=1,
    )

    try:
        yield client
    finally:
        client.close()
        await client.wait_closed()
