import contextlib

import aioboto3

from app.settings.config import settings


@contextlib.asynccontextmanager
async def get_s3_resource():
    async with aioboto3.resource(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net',
        region_name='ru-central1',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    ) as s3_res:
        try:
            yield s3_res
        finally:
            pass
