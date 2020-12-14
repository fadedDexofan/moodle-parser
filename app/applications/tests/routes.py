import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.applications.tests.dto import TestParseRequest
from app.applications.tests.models import Test, Test_Pydantic
from app.applications.tests.services import get_test_by_id, parse_test_into_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post('/', response_model=None, status_code=202, tags=['tests'])
async def parse_test(
    parse_request: TestParseRequest,
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(parse_test_into_db, parse_request=parse_request)
    return {}


@router.get('/{test_id}', response_model=Test_Pydantic, status_code=200, tags=['tests'])
async def read_test_by_id(test_id: int):
    test = await get_test_by_id(test_id)
    if not test:
        raise HTTPException(
            status_code=404,
            detail='Тест с указанным ID не найден',
        )
    return await Test_Pydantic.from_tortoise_orm(test)


@router.delete('/{test_id}', status_code=204, tags=['tests'])
async def delete_test(test_id: int):
    test = await Test.get(test_id=test_id)
    await test.delete()
    return None
