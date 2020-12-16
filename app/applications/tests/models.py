from tortoise import Tortoise, fields
from tortoise.contrib.pydantic import pydantic_model_creator

from app.core.base.base_models import BaseDBModel
from app.parser.dto import CompletionStatus


class Test(BaseDBModel):
    name = fields.CharField(max_length=255, index=True)
    path = fields.CharField(max_length=1024, index=True)
    test_id = fields.IntField()
    domain = fields.CharField(max_length=127)

    questions: fields.ReverseRelation['Question']

    class Meta:
        unique_together = ('test_id', 'domain')
        indexes = ('test_id', 'domain')

    def __str__(self) -> str:
        return f'[{self.test_id}] {self.name}'


class Question(BaseDBModel):
    test: fields.ForeignKeyRelation[Test] = fields.ForeignKeyField(
        model_name='models.Test',
        related_name='questions',
    )

    question_id = fields.IntField(unique=True, index=True)
    screenshot = fields.CharField(max_length=256)
    status = fields.CharEnumField(CompletionStatus)

    def __str__(self) -> str:
        return f'[{self.status}] Question {self.question_id}'


Tortoise.init_models(['app.applications.tests.models'], 'models')

Test_Pydantic = pydantic_model_creator(Test)
