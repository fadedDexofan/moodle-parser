from pydantic import BaseModel


class TestParseRequest(BaseModel):
    auth_cookie: str
    test_url: str
