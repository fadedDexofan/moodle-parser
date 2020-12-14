import logging
from typing import Optional

from pydantic import ValidationError
from tortoise.query_utils import Prefetch
from tortoise.transactions import atomic

from app.applications.tests.dto import TestParseRequest
from app.applications.tests.models import Question, Test
from app.parser.dto import CompletionStatus, QuestionDTO, TestResultDTO
from app.parser.exceptions import ParseException
from app.parser.logic import parse_test

logger = logging.getLogger(__name__)


async def create_new_question(test: Test, question_dto: QuestionDTO) -> None:
    await Question.create(
        test=test,
        question_id=question_dto.id,
        screenshot='',
        status=question_dto.status,
    )


async def update_question(question: Question, question_dto: QuestionDTO) -> None:
    old_status = question.status
    new_status = question_dto.status

    if old_status == CompletionStatus.CORRECT:
        return

    if old_status == CompletionStatus.PARTIALLY_CORRECT and new_status != CompletionStatus.CORRECT:
        return

    question.screenshot = question_dto.screenshot
    question.status = question_dto.status
    await question.save()


@atomic()
async def save_new_test(test_result: TestResultDTO):
    test = await Test.create(
        test_id=test_result.id,
        name=test_result.name,
        domain=test_result.domain,
    )

    for question_dto in test_result.questions:
        await create_new_question(test, question_dto)


@atomic()
async def update_existing_test(test: Test, test_result: TestResultDTO):
    existing_questions = {
        question.question_id: question
        async for question in test.questions
    }

    for question_dto in test_result.questions:
        if existing_question := existing_questions.get(question_dto.id):
            await update_question(existing_question, question_dto)
        else:
            await create_new_question(test, question_dto)


async def parse_test_into_db(parse_request: TestParseRequest) -> None:
    try:
        test_result = await parse_test(
            cookie=parse_request.auth_cookie,
            test_attempt_url=parse_request.test_url,
        )
    except ParseException:
        logger.exception('Ошибка парсинга результатов теста %s', parse_request.test_url)
        raise
    except ValidationError:
        logger.exception('Ошибка валидации данных теста')
        raise

    existing_test = await Test.get_or_none(test_id=test_result.id, domain=test_result.domain)
    if existing_test:
        await update_existing_test(existing_test, test_result)
    else:
        await save_new_test(test_result)


async def get_test_by_id_and_domain(test_id: int, domain: str) -> Optional[Test]:
    return await Test.get_or_none(test_id=test_id, domain=domain).prefetch_related(
        Prefetch('questions', queryset=Question.all().order_by('question_id')),
    )
