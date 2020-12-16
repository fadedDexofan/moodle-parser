import logging
from typing import List
from urllib.parse import parse_qsl

import httpx
from pyppeteer.page import Page

from app.parser.dto import CompletionStatus, QuestionDTO, TestInfoDTO, TestResultDTO
from app.parser.exceptions import ParseException
from app.parser.helpers import (
    get_headless_browser, get_test_info_from_attempt_url,
)

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0',
}


# id вопроса в бд это qid в инпуте кнопки поставить флаг
# qubaid это "The id of the question usage".
#  Является id вопроса на странице (id в html тэгах) это qubaid + slot,
# qaid id попытки ответа на конкретный вопрос?


async def request_test_page(cookie: str, test_attempt_url: str) -> str:
    cookies = {'MoodleSession': cookie}

    async with httpx.AsyncClient(headers=HEADERS, cookies=cookies, max_redirects=0) as client:
        try:
            response = await client.get(test_attempt_url)
            response.raise_for_status()
        except httpx.RequestError as exc:
            raise ParseException(f'Error while requesting : {exc.request.url!r}.')
        except httpx.HTTPStatusError as exc:
            raise ParseException(
                f'Error response {exc.response.status_code} while requesting {exc.request.url!r}.',
            )
        else:
            return response.text


def get_completion_status(classes_str: str) -> CompletionStatus:
    classes = set(classes_str.split(' '))

    if 'correct' in classes:
        return CompletionStatus.CORRECT
    elif 'partiallycorrect' in classes:
        return CompletionStatus.PARTIALLY_CORRECT
    elif 'incorrect' in classes:
        return CompletionStatus.INCORRECT
    else:
        raise ParseException(f'Неизвестный статус завершения: {classes}')


async def parse_questions(attempt_page: Page) -> List[QuestionDTO]:
    questions = []
    for el in await attempt_page.querySelectorAll('div[id^="question-"]'):
        flag_input_value = await el.querySelectorEval(
            'input.questionflagpostdata',
            pageFunction='x => x.value',
        )
        question_id: str = dict(parse_qsl(flag_input_value))['qid']
        question_el_classes: str = await attempt_page.evaluate('el => el.className', el)

        question = QuestionDTO(
            id=int(question_id),
            screenshot=await el.screenshot(),
            status=get_completion_status(question_el_classes),
        )
        questions.append(question)

    return questions


async def parse_test(cookie: str, test_attempt_url: str) -> TestResultDTO:
    test_url_info = get_test_info_from_attempt_url(test_attempt_url)

    await request_test_page(cookie, test_attempt_url)

    async with get_headless_browser() as browser:
        page: Page = await browser.newPage()

        await page.setUserAgent(HEADERS['User-Agent'])
        session_cookie = {
            'name': 'MoodleSession',
            'value': cookie,
            'domain': test_url_info.domain,
        }
        await page.setCookie(session_cookie)
        await page.goto(test_attempt_url, {'waitUntil': 'networkidle2'})

        test_name: str = await page.querySelectorEval(
            selector='#page-navbar li:last-child',
            pageFunction='el => el.innerText',
        )

        questions = await parse_questions(page)

    return TestResultDTO(
        info=TestInfoDTO(
            id=test_url_info.test_id,
            name=test_name.strip(),
            path='',
            domain=test_url_info.domain,
        ),
        questions=questions,
    )
