from unicodedata import normalize
from urllib.parse import parse_qsl, urlsplit

from bs4 import Tag

from app.parser.exceptions import ParseException


def get_test_id_from_url(url: str) -> int:
    url_params = dict(parse_qsl(urlsplit(url).query))
    if 'cmid' not in url_params or 'attempt' not in url_params:
        raise ParseException('Некорректная ссылка на результаты теста')
    return int(url_params['cmid'])


def normalize_unicode(unicode_str: str) -> str:
    return normalize('NFKD', unicode_str).strip()


def get_tag_text(tag: Tag) -> str:
    text = tag.get_text(strip=True)
    return normalize_unicode(text)
