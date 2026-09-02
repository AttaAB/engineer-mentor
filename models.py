from pydantic import BaseModel

class MentorQuestion(BaseModel):
  category: str
  question: str

class MentorResponse(BaseModel):
  questions: list[MentorQuestion]

question = MentorQuestion(
    category="correctness",
    question="What happens if the request fails?"
)

print(question.category)  # Output: correctness