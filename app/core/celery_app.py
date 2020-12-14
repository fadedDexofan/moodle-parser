import logging

import celery_pool_asyncio  # noqa
from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
from tortoise import Tortoise

from app.core.init_app import get_apps_list, init_db

logger = logging.getLogger(__name__)

celery_pool_asyncio.__package__  # noqa

celery_app = Celery('celery_worker')
celery_app.config_from_object('app.settings.celery_config')

celery_app.autodiscover_tasks(['app.core', *get_apps_list()])


@worker_process_init.connect
async def startup(**kwargs):
    logger.info('Initializing database connection for worker.')
    await init_db()


@worker_process_shutdown.connect
async def shutdown(**kwargs):
    logger.info('Closing database connection for worker.')
    await Tortoise.close_connections()
