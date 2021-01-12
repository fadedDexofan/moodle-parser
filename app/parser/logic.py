import logging
import re
from decimal import Decimal
from functools import lru_cache
from typing import Dict, List, Set
from urllib.parse import parse_qsl

import httpx
from pyppeteer.browser import Browser
from pyppeteer.element_handle import ElementHandle
from pyppeteer.page import Page
from selectolax.parser import HTMLParser, Node

from app.lib.utils import decimal_quantize
from app.parser.constants import (
    FLAG_INPUT_SELECTOR, HEADERS, NOT_ANSWERED_CLASS,
    QUESTIONS_SELECTOR,
)
from app.parser.dto import CompletionStatus, QuestionDTO, TestInfoDTO, TestResultDTO
from app.parser.exceptions import AllQuestionsExists, ParseException
from app.parser.helpers import (
    get_element_property, get_headless_browser, get_test_info_from_attempt_url,
)

logger = logging.getLogger(__name__)

MARK_REGEX = re.compile(r'(\d+(?:\.\d+))')


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


async def _get_question_completion_status(question_element: ElementHandle) -> CompletionStatus:
    classes_str: str = await get_element_property(question_element, 'className')
    classes = set(classes_str.split(' '))

    if NOT_ANSWERED_CLASS in classes:
        return CompletionStatus.NOT_ANSWERED

    mark_str = await question_element.querySelectorEval('div.grade', 'el => el.innerText')
    return _get_completion_status_by_mark(mark_str)


def _get_completion_status_by_mark(mark_str: str) -> CompletionStatus:
    mark_str = mark_str.replace(',', '.')
    marks_match = MARK_REGEX.findall(mark_str)

    current_mark = decimal_quantize(marks_match[0])
    max_mark = decimal_quantize(marks_match[1])

    if current_mark == max_mark:
        return CompletionStatus.CORRECT
    elif Decimal(0) < current_mark < max_mark:
        return CompletionStatus.PARTIALLY_CORRECT
    else:
        return CompletionStatus.INCORRECT


def _get_test_id_from_flag_input(flag_input_value: str) -> int:
    question_id = dict(parse_qsl(flag_input_value))['qid']
    return int(question_id)


async def _get_question_id_from_question_element(question_element: ElementHandle) -> int:
    flag_input_value = await question_element.querySelectorEval(
        selector=FLAG_INPUT_SELECTOR,
        pageFunction='x => x.value',
    )
    return _get_test_id_from_flag_input(flag_input_value)


async def _parse_questions(
    questions_elements: List[ElementHandle],
    questions_for_skip: Set[int],
) -> List[QuestionDTO]:
    questions: List[QuestionDTO] = []
    for question_element in questions_elements:
        question_id = await _get_question_id_from_question_element(question_element)

        if question_id in questions_for_skip:
            logger.debug('[%s] Question #%d already parsed, skipping')
            continue

        question_dto = QuestionDTO(
            id=question_id,
            screenshot=await question_element.screenshot(),
            status=await _get_question_completion_status(question_element),
        )
        questions.append(question_dto)

    return questions


def get_test_questions_for_skip(
    test_page: str,
    existing_test_questions: List[int],
) -> Set[int]:
    tree = HTMLParser(test_page)

    page_questions: List[int] = []
    for question_el in tree.css(QUESTIONS_SELECTOR):  # type: Node
        flag_input_value = question_el.css_first(FLAG_INPUT_SELECTOR).attributes['value']
        page_questions.append(_get_test_id_from_flag_input(flag_input_value))

    existing_test_questions_set = set(existing_test_questions)
    page_questions_set = set(page_questions)

    return existing_test_questions_set.intersection(page_questions_set)


@lru_cache
def _get_session_cookie(cookie: str, domain: str) -> Dict[str, str]:
    return {
        'name': 'MoodleSession',
        'value': cookie,
        'domain': domain,
    }


async def _navigate_to_test_page(
    browser: Browser,
    attempt_url: str,
    session_cookie: Dict[str, str],
) -> Page:
    page: Page = await browser.newPage()
    await page.setUserAgent(HEADERS['User-Agent'])
    await page.setCookie(session_cookie)
    await page.goto(attempt_url, {'waitUntil': 'networkidle2'})

    return page


async def _get_info_from_navbar(page: Page) -> str:
    test_name = await page.querySelectorEval(
        selector='#page-navbar li:last-child',
        pageFunction='el => el.innerText',
    )
    # TODO: Parse test path and return DTO
    return test_name.strip()


async def parse_test(
    cookie: str,
    test_attempt_url: str,
    existing_test_questions: List[int],
) -> TestResultDTO:
    test_url_info = get_test_info_from_attempt_url(test_attempt_url)
    test_page = await request_test_page(cookie, test_attempt_url)

    if existing_test_questions:
        questions_for_skip = get_test_questions_for_skip(test_page, existing_test_questions)
        if len(questions_for_skip) == len(existing_test_questions):
            raise AllQuestionsExists()
    else:
        questions_for_skip = set()

    async with get_headless_browser() as browser:
        session_cookie = _get_session_cookie(cookie, test_url_info.domain)
        page = await _navigate_to_test_page(browser, test_attempt_url, session_cookie)

        test_info = TestInfoDTO(
            id=test_url_info.test_id,
            name=await _get_info_from_navbar(page),
            path='',
            domain=test_url_info.domain,
        )

        questions_elements = await page.querySelectorAll(QUESTIONS_SELECTOR)
        questions = await _parse_questions(questions_elements, questions_for_skip)

    return TestResultDTO(
        info=test_info,
        questions=questions,
    )
