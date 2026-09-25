from typing import Literal
from pydantic import BaseModel

Category = Literal[
    "correctness",
    "reliability",
    "architecture",
    "performance",
    "maintainability",
]


class MentorQuestion(BaseModel):
    category: Category
    question: str


class MentorResponse(BaseModel):
    questions: list[MentorQuestion]