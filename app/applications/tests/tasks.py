import asyncio

from celery.utils.log import get_task_logger

from app.applications.tests.dto import TestParseRequest
from app.applications.tests.services import parse_test_into_db
from app.core.celery_app import celery_app
from app.lib.celery_lock import sync_redis_lock
from app.parser.exceptions import ParseException

logger = get_task_logger(__name__)


@celery_app.task(
    bind=True,
    autoretry_for=(ParseException,),
    retry_kwargs={'max_retries': 2},
    time_limit=60,
)
def parse_quiz_task(self, parse_request: TestParseRequest) -> None:
    task_id = self.request.id
    with sync_redis_lock(f'{task_id}-lock') as acquired:
        if acquired:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(parse_test_into_db(parse_request))
        else:
            logger.info('Task %s already processing', task_id)
