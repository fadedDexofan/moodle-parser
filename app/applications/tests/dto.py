from pydantic import BaseModel


class TestParseRequest(BaseModel):
    auth_cookie: str
    attempt_url: str


class TestSearchRequest(BaseModel):
    domain: str
    test_id: int
