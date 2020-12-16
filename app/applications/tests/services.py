import logging
import mimetypes
import os
from contextvars import ContextVar
from dataclasses import dataclass
from io import BytesIO
from typing import Any

from pydantic import ValidationError
from tortoise.query_utils import Prefetch
from tortoise.transactions import atomic

from app.applications.tests.dto import TestParseRequest, TestSearchRequest
from app.applications.tests.models import Question, Test
from app.lib.aws import get_s3_resource
from app.parser.dto import CompletionStatus, QuestionDTO, TestInfoDTO, TestResultDTO
from app.parser.exceptions import ParseException
from app.parser.helpers import get_test_info_from_attempt_url
from app.parser.logic import parse_test

logger = logging.getLogger(__name__)


@dataclass
class S3Context:
    resource: Any
    bucket: Any


s3_context: ContextVar[S3Context] = ContextVar('s3_context')


async def upload_question_screenshot(test_info_dto: TestInfoDTO, question_dto: QuestionDTO) -> str:
    s3_ctx = s3_context.get()
    bucket = s3_ctx.bucket

    screenshot_name = f'{test_info_dto.domain}/{test_info_dto.id}/{question_dto.id}.png'
    content_type, encoding = mimetypes.guess_type(screenshot_name)
    params = {
        'ContentType': content_type,
        'ACL': 'public-read',
    }

    s3_obj = await bucket.Object(screenshot_name)
    screenshot_file = BytesIO(question_dto.screenshot)
    screenshot_file.seek(0, os.SEEK_SET)
    await s3_obj.upload_fileobj(screenshot_file, ExtraArgs=params)

    return '{}/{}/{}'.format(
        bucket.meta.client.meta.endpoint_url,
        bucket.name,
        screenshot_name,
    )


async def create_new_question(
    test: Test,
    test_info_dto: TestInfoDTO,
    question_dto: QuestionDTO,
) -> None:
    await Question.create(
        test=test,
        question_id=question_dto.id,
        screenshot=await upload_question_screenshot(test_info_dto, question_dto),
        status=question_dto.status,
    )


async def update_question(
    test_info_dto: TestInfoDTO,
    question: Question,
    question_dto: QuestionDTO,
) -> None:
    old_status = question.status
    new_status = question_dto.status

    if old_status == CompletionStatus.CORRECT:
        return

    if old_status == CompletionStatus.PARTIALLY_CORRECT and new_status != CompletionStatus.CORRECT:
        return

    question.screenshot = await upload_question_screenshot(test_info_dto, question_dto)
    question.status = question_dto.status
    await question.save()


@atomic()
async def save_new_test(test_result: TestResultDTO):
    test_info = test_result.info
    test = await Test.create(
        test_id=test_info.id,
        path='',
        name=test_info.name,
        domain=test_info.domain,
    )

    for question_dto in test_result.questions:
        await create_new_question(test, test_info, question_dto)


@atomic()
async def update_existing_test(test: Test, test_result: TestResultDTO):
    existing_questions = {
        question.question_id: question
        async for question in test.questions
    }
    test_info = test_result.info

    for question_dto in test_result.questions:
        if existing_question := existing_questions.get(question_dto.id):
            await update_question(test_info, existing_question, question_dto)
        else:
            await create_new_question(test, test_info, question_dto)


async def enqueue_parse_task(parse_request: TestParseRequest) -> None:
    from app.applications.tests.tasks import parse_quiz_task

    test_url_info = get_test_info_from_attempt_url(parse_request.attempt_url)
    job_id = '{}-{}-{}'.format(
        test_url_info.domain,
        test_url_info.test_id,
        test_url_info.attempt_id,
    )

    parse_quiz_task.apply_async((parse_request,), task_id=job_id)


async def parse_test_into_db(parse_request: TestParseRequest) -> None:
    try:
        test_result = await parse_test(
            cookie=parse_request.auth_cookie,
            test_attempt_url=parse_request.attempt_url,
        )
    except ParseException:
        logger.exception('Ошибка парсинга результатов теста %s', parse_request.attempt_url)
        raise
    except ValidationError:
        logger.exception('Ошибка валидации данных теста')
        raise

    test_info = test_result.info
    existing_test = await Test.get_or_none(test_id=test_info.id, domain=test_info.domain)

    async with get_s3_resource() as s3_res:
        bucket = await s3_res.Bucket('questions')
        ctx = S3Context(s3_res, bucket)
        ctx_token = s3_context.set(ctx)

        if existing_test:
            await update_existing_test(existing_test, test_result)
        else:
            await save_new_test(test_result)

        s3_context.reset(ctx_token)


async def search_test_by_request(search_request: TestSearchRequest) -> Test:
    return await Test.get(
        test_id=search_request.test_id,
        domain=search_request.domain,
    ).prefetch_related(
        Prefetch('questions', queryset=Question.all().order_by('question_id')),
    )
