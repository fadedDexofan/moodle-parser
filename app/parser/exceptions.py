class ParseException(Exception):
    pass


class QuestionNotAnswered(Exception):
    def __init__(self, question_id: int):
        self.question_id = question_id


class AllQuestionsExists(Exception):
    pass
