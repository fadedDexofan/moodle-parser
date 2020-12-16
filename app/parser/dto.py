from enum import Enum
from typing import List

from pydantic import BaseModel


class CompletionStatus(str, Enum):
    CORRECT = 'CORRECT'
    PARTIALLY_CORRECT = 'PARTIALLY_CORRECT'
    INCORRECT = 'INCORRECT'


class QuestionDTO(BaseModel):
    id: int
    screenshot: bytes
    status: CompletionStatus


class TestInfoDTO(BaseModel):
    id: int
    name: str
    path: str
    domain: str


class TestResultDTO(BaseModel):
    info: TestInfoDTO
    questions: List[QuestionDTO]


class TestUrlInfoDTO(BaseModel):
    test_id: int
    attempt_id: int
    domain: str
