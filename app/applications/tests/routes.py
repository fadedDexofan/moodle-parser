import logging

from fastapi import APIRouter
from starlette.background import BackgroundTasks

from app.applications.tests.dto import TestParseRequest, TestSearchRequest
from app.applications.tests.models import Test, Test_Pydantic
from app.applications.tests.services import enqueue_parse_task, search_test_by_request

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post('/', response_model=None, status_code=202, tags=['tests'])
async def parse_test(
    parse_request: TestParseRequest,
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(enqueue_parse_task, parse_request)
    return {}


@router.post('/search', response_model=Test_Pydantic, status_code=200, tags=['tests'])
async def search_test(search_request: TestSearchRequest):
    test = await search_test_by_request(search_request)
    return await Test_Pydantic.from_tortoise_orm(test)


@router.delete('/{test_id}', status_code=204, tags=['tests'])
async def delete_test(test_id: int):
    test = await Test.get(test_id=test_id)
    await test.delete()
    return None
