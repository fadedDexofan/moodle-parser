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


class TestResultDTO(BaseModel):
    id: int
    name: str
    domain: str
    questions: List[QuestionDTO]
