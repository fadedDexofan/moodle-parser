from tortoise import Tortoise, fields
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.fields import SET_NULL

from app.core.base.base_models import BaseDBModel
from app.parser.dto import CompletionStatus


class Test(BaseDBModel):
    name = fields.CharField(max_length=255, index=True)
    path = fields.CharField(max_length=1024, index=True)
    test_id = fields.IntField()
    domain = fields.CharField(max_length=255)

    questions: fields.ReverseRelation['Question']

    class Meta:
        unique_together = ('test_id', 'domain')
        indexes = ('test_id', 'domain')

    def __str__(self) -> str:
        return f'[{self.test_id}] {self.name}'


class Question(BaseDBModel):
    tests: fields.ManyToManyRelation[Test] = fields.ManyToManyField(
        model_name='models.Test',
        related_name='questions',
        through='question_tests',
        on_delete=SET_NULL,
        null=True,
    )

    domain = fields.CharField(max_length=255)
    question_id = fields.IntField()
    screenshot = fields.CharField(max_length=256)
    status = fields.CharEnumField(CompletionStatus)

    class Meta:
        unique_together = ('question_id', 'domain')
        indexes = ('question_id', 'domain')

    def __str__(self) -> str:
        return f'[{self.status}] Question {self.question_id}'


Tortoise.init_models(['app.applications.tests.models'], 'models')

Test_Pydantic = pydantic_model_creator(Test)
