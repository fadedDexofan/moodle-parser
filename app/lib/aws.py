import contextlib
import mimetypes
import os
from io import BytesIO
from typing import Any

import aioboto3

from app.settings.config import settings


@contextlib.asynccontextmanager
async def get_s3_resource():
    async with aioboto3.resource(
        service_name='s3',
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        region_name=settings.AWS_S3_REGION_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    ) as s3_res:
        try:
            yield s3_res
        finally:
            pass


async def upload_file_to_s3(bucket: Any, file: BytesIO, file_name: str) -> str:
    file.seek(0, os.SEEK_SET)

    s3_obj = await bucket.Object(file_name)
    await s3_obj.upload_fileobj(
        Fileobj=file,
        ExtraArgs={
            'ContentType': mimetypes.guess_type(file_name)[0],
            'ACL': 'public-read',
        },
    )

    return '{base_url}/{bucket_name}/{file_name}'.format(
        base_url=bucket.meta.client.meta.endpoint_url,
        bucket_name=bucket.name,
        file_name=file_name,
    )
