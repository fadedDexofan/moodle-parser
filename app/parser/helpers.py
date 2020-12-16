import contextlib
from unicodedata import normalize
from urllib.parse import parse_qsl, urlsplit

from pyppeteer import launch
from pyppeteer.browser import Browser

from app.parser.dto import TestUrlInfoDTO
from app.parser.exceptions import ParseException
from app.settings.config import settings


def get_test_info_from_attempt_url(url: str) -> TestUrlInfoDTO:
    split_result = urlsplit(url)
    url_params = dict(parse_qsl(split_result.query))

    if not (url_params.get('cmid') and url_params.get('attempt')):
        raise ParseException('Некорректная ссылка на результаты теста')

    return TestUrlInfoDTO(
        test_id=int(url_params['cmid']),
        attempt_id=int(url_params['attempt']),
        domain=split_result.netloc,
    )


def normalize_unicode(unicode_str: str) -> str:
    return normalize('NFKD', unicode_str).strip()


@contextlib.asynccontextmanager
async def get_headless_browser() -> Browser:
    default_viewport = {'width': 1920, 'height': 20000, 'deviceScaleFactor': 1}
    browser = await launch({
        'defaultViewport': default_viewport,
        'executablePath': settings.CHROMIUM_PATH,
    })
    try:
        yield browser
    finally:
        await browser.close()
