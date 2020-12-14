from app.applications.tests.dto import TestParseRequest
from app.applications.tests.services import parse_test_into_db
from app.core.celery_app import celery_app
from app.parser.exceptions import ParseException


@celery_app.task(
    autoretry_for=(ParseException,),
    retry_kwargs={'max_retries': 5},
    time_limit=120,
)
async def parse_quiz(parse_request: TestParseRequest) -> None:
    await parse_test_into_db(parse_request)
