import logging
from asyncio import get_event_loop
from io import BytesIO
from typing import Awaitable, Callable, Dict, Iterable, List, Optional, Tuple

import httpx
from bs4 import BeautifulSoup, NavigableString, Tag
from pyppeteer import launch
from pyppeteer.element_handle import ElementHandle

from app.parser.dto import AnswerDTO, CompletionStatus, QuestionDTO, QuestionType, TestResultDTO
from app.parser.exceptions import ParseException
from app.parser.helpers import get_tag_text, get_test_id_from_url, normalize_unicode

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0',
}


# id вопроса в бд это qid в инпуте кнопки поставить флаг
# qubaid это "The id of the question usage".
#  Является id вопроса на странице (id в html тэгах) это qubaid + slot,
# qaid id попытки ответа на конкретный вопрос?
#


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


async def parse_match_answers(question_tag: Tag) -> List[AnswerDTO]:
    answers_tags = question_tag.select('table.answer tr')

    answers = []
    answer_tag: Tag
    for answer_tag in answers_tags:
        match_text = None
        match_image = None

        match_tag = answer_tag.contents[0]
        if img_tag := match_tag.select_one('img'):
            match_image = img_tag.attrs['src']
        else:
            match_text = get_tag_text(match_tag.select_one('p'))

        match_answer_tag = answer_tag.contents[1]
        answer_text = get_tag_text(match_answer_tag.select_one('[selected="selected"]'))

        answer = AnswerDTO(
            answer=answer_text,
            match_text=match_text,
            match_image=match_image,
            status=get_completion_status(match_answer_tag.attrs['class']),
        )
        answers.append(answer)

    return answers


async def parse_multi_answer_answers(question_tag: Tag) -> List[AnswerDTO]:
    answers_tags = question_tag.select('span.subquestion')

    answers = []
    for answer_tag in answers_tags:
        if input_tag := answer_tag.select_one('input'):
            status = get_completion_status(input_tag.attrs['class'])
            answer_text = normalize_unicode(input_tag.attrs['value'])
        elif selector_tag := answer_tag.select_one('select'):
            status = get_completion_status(selector_tag.attrs['class'])
            selector_selected = selector_tag.select_one('[selected="selected"]')
            answer_text = get_tag_text(selector_selected)
        else:
            logger.warning('Unsupported MultiAnswer answer selector type')
            continue

        pre_text = ''
        post_text = ''

        if isinstance(answer_tag.previous_sibling, NavigableString):
            pre_text = normalize_unicode(answer_tag.previous_sibling)
        if isinstance(answer_tag.next_sibling, NavigableString):
            post_text = normalize_unicode(answer_tag.next_sibling)

        full_answer_text = f'{pre_text} {answer_text} {post_text}'.strip()

        answer = AnswerDTO(answer=full_answer_text, status=status)
        answers.append(answer)

    return answers


async def parse_choice_answers(question_tag: Tag) -> List[AnswerDTO]:
    answers_tags = question_tag.select('div.answer')

    answers = []
    for answer_tag in answers_tags:
        classes = set(question_tag.attrs['class'])
        if 'truefalse' in classes:
            answer_text = get_tag_text(answer_tag.select_one('label'))
        else:
            answer_text = get_tag_text(answer_tag.select_one('p'))

        answer = AnswerDTO(answer=answer_text, status=get_completion_status(classes))
        answers.append(answer)

    return answers


async def parse_answers(question_tag: Tag, question_type: QuestionType) -> List[AnswerDTO]:
    answers_parse_funcs: Dict[QuestionType, Callable[[Tag], Awaitable[List[AnswerDTO]]]] = {
        QuestionType.SINGLE_CHOICE: parse_choice_answers,
        QuestionType.MULTI_CHOICE: parse_choice_answers,
        QuestionType.MATCH: parse_match_answers,
        QuestionType.MULTI_ANSWER: parse_multi_answer_answers,
    }
    return await answers_parse_funcs[question_type](question_tag)


async def get_question_text(
    question_tag: Tag,
    question_type: QuestionType,
) -> Tuple[Optional[str], str]:
    if question_type == QuestionType.MULTI_ANSWER:
        if media_plugin_tag := question_tag.select_one('div.mediaplugin'):
            media_plugin_tag.extract()
        return None, get_tag_text(question_tag.select_one('p'))

    question_text_tags = question_tag.select('div.qtext p')
    if len(question_text_tags) > 1:
        pre_question = get_tag_text(question_text_tags[0])
        question_text = get_tag_text(question_text_tags[1])
    else:
        pre_question = None
        question_text = get_tag_text(question_text_tags[0])

    return pre_question, question_text


def get_question_type(question_tag: Tag) -> Optional[QuestionType]:
    question_classes = set(question_tag.attrs['class'])

    if question_classes.intersection({'multichoice', 'truefalse'}):
        return QuestionType.MULTI_CHOICE
    elif 'match' in question_classes:
        return QuestionType.MATCH
    elif 'multianswer' in question_classes:
        return QuestionType.MULTI_ANSWER
    else:
        return None


def get_completion_status(classes: Iterable[str]) -> CompletionStatus:
    if not isinstance(classes, set):
        classes = set(classes)
    if 'correct' in classes:
        return CompletionStatus.CORRECT
    elif 'partiallycorrect' in classes:
        return CompletionStatus.PARTIALLY_CORRECT
    elif 'incorrect' in classes:
        return CompletionStatus.INCORRECT
    else:
        raise ParseException(f'Неизвестный статус завершения: {classes}')


async def parse_questions(questions_tags: List[Tag]) -> List[QuestionDTO]:
    questions: List[QuestionDTO] = []

    for question_tag in questions_tags:
        question_id = question_tag.attrs['id'].replace('question-', '')

        question_type = get_question_type(question_tag)
        if not question_type:
            logger.warning('Unsupported question type for id: %s', question_id)
            continue

        pre_question, question_text = await get_question_text(question_tag, question_type)

        answers = await parse_answers(question_tag, question_type)
        if question_type == QuestionType.MULTI_CHOICE and len(answers) == 1:
            question_type = QuestionType.SINGLE_CHOICE

        question = QuestionDTO(
            id=question_id,
            pre_question=pre_question,
            question=question_text,
            type=question_type,
            answers=answers,
            status=get_completion_status(question_tag.attrs['class']),
        )

        questions.append(question)

    return questions


async def parse_test(cookie: str, test_attempt_url: str) -> TestResultDTO:
    test_id = get_test_id_from_url(test_attempt_url)

    page = await request_test_page(cookie, test_attempt_url)
    soup = BeautifulSoup(page, features='lxml')

    test_name = get_tag_text(soup.select_one('#page-navbar li:last-child'))
    questions_tags = soup.select('div.que')
    questions = await parse_questions(questions_tags)

    return TestResultDTO(
        test_name=test_name,
        test_id=test_id,
        questions=questions,
    )


async def make_question_screenshot(question_el: ElementHandle) -> bytes:
    return await question_el.screenshot()


async def main():
    cookie = '3b5bj374lsa0ngphd8emfch3t4'
    url = 'https://sdo.sut.ru/mod/quiz/review.php?attempt=665097&cmid=31806'
    test_id = get_test_id_from_url(url)

    default_viewport = {'width': 1920, 'height': 10000, 'deviceScaleFactor': 1}

    browser = await launch({'defaultViewport': default_viewport})
    page = await browser.newPage()

    await page.setUserAgent(HEADERS['User-Agent'])
    await page.setCookie({'name': 'MoodleSession', 'value': cookie, 'domain': 'sdo.sut.ru'})
    await page.goto(url, {'waitUntil': 'networkidle2'})

    # soup = BeautifulSoup(await page.content(), features='lxml')

    f = open('questions/hash2.txt', 'w')

    for el in await page.querySelectorAll('div[id^="question-"]'):
        q_id = await page.evaluate('x => x.id', el)
        image_buffer = BytesIO(await el.screenshot({'path': f'questions/{q_id}.png'}))

    f.close()

    await browser.close()

    # await parse_test(cookie, url)


if __name__ == '__main__':
    loop = get_event_loop()
    loop.run_until_complete(main())
