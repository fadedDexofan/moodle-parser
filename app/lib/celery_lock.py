import time
from contextlib import contextmanager

from app.lib.redis import redis_sync_client

LOCK_EXPIRE = 5 * 60  # 5 min


@contextmanager
def sync_redis_lock(lock_id: str):
    with redis_sync_client() as redis_client:
        timeout_at = time.monotonic() + LOCK_EXPIRE - 3
        status = redis_client.set(lock_id, 'lock', nx=True, ex=LOCK_EXPIRE)
        try:
            yield status
        finally:
            if time.monotonic() < timeout_at and status:
                # don't release the lock if we didn't acquire it or if timeout already expired
                redis_client.delete(lock_id)
