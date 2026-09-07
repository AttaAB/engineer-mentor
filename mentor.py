from dotenv import load_dotenv
from openai import OpenAI
from models import MentorResponse

load_dotenv()

client = OpenAI()

def generate_mentor_questions(pr_title, context):
  prompt = f""" 
  You are a software engineering mentor reviewing an entire pull request.

  Your goal is to identify the highest-value engineering decisions in
  the change and ask questions that cause the developer to reason about
  their assumptions and trade-offs.

  Review the pull request as one logical change. Tests should be used
  primarily to infer intended behavior.

  Ask 0–3 questions. Prefer one strong question over several weaker ones.
  Return NO_QUESTIONS if there is nothing meaningful to discuss.

  Prioritize:
  1. correctness and behavioral contracts
  2. reliability and error handling
  3. architecture and API design
  4. performance
  5. maintainability

  A good question:
  - is directly supported by the supplied changes
  - focuses on the central decision before secondary edge cases
  - asks the developer to derive consequences rather than stating them
  - could meaningfully affect the implementation or review

  Avoid:
  - speculative or unlikely edge cases
  - duplicate questions
  - trivial style feedback
  - questions already answered by the diff
  - giving the consequence or solution inside the question
  - evaluating each changed file independently

  You only have the supplied PR context. When information is missing,
  question the assumption rather than claiming a defect exists.

  Return an empty questions list if there are no meaningful engineering decisions worth questioning.

  Otherwise output only a numbered list of questions.

  Pull Request Title:
  {pr_title}

  Pull Request Changes:
  {context} 
  """
  response = client.responses.parse(
    model="gpt-5.6-luna",
    input=prompt,
    text_format=MentorResponse
  )
  
  return response.output_parsed

if __name__ == "__main__":
  patch = """
  def find_user(users, user_id):
    for user in users:
      if user["id"] == user_id:
        return user
  """
  mentor_reposnse = generate_mentor_questions("example-file", patch)
  print(mentor_reposnse.questions)