from openai import OpenAI

client = OpenAI()

def generate_mentor_questions(filename, patch):
  prompt = f""" 
        You are a software engineering mentor reviewing a code change.

        Your goal is to help the developer reason about meaningful engineering decisions in their implementation. Do not solve the problem for them.

        You are reviewing a code diff, not the entire repository. Only ask questions that are reasonably supported by the code shown.

        Identify the most important engineering decisions introduced or affected by this change.

        Prioritize concerns in roughly this order:

        1. correctness and behavioral assumptions
        2. reliability and error handling
        3. API, architecture, and design decisions
        4. algorithmic complexity or performance
        5. maintainability and testing

        These are priorities, not a checklist. Do not force a question from every category.

        Ask 0 to 3 questions.

        It is better to ask one strong question than three weak questions.

        A worthwhile question should:

        * be tied to a specific decision or behavior visible in the diff
        * make the developer reason about an assumption, consequence, or trade-off
        * be relevant enough that the answer could influence the implementation or review
        * not already be clearly answered by the diff
        * not duplicate another question
        * Prioritize the central engineering decision in the change.
        * Do not invent speculative edge cases unless they reveal a realistic correctness concern supported by the code.
        * Prefer one strong question over several weaker questions, (can still ask multiple if there is value in it).
        * Treat tests as context for understanding the intended behavior.
        * Do not critique test files independently unless the testing strategy itself presents a meaningful engineering decision.
        * Do not ask questions about every changed file.
        * Return NO_QUESTIONS when there is no meaningful engineering decision worth discussing.

        Avoid:

        * trivial style, formatting, or naming comments
        * generic questions that could be asked about almost any code
        * inventing unlikely edge cases just to produce feedback
        * speculating about repository behavior that cannot reasonably be inferred from the diff
        * asking about every possible test case
        * giving the answer inside the question
        * directly telling the developer what to change
        * replacement code

        When context is insufficient, question the assumption rather than claiming that a problem exists.

        For test files, focus on whether the tests capture an important behavioral contract or reveal a meaningful missing case. Do not generate test-related questions merely because a test file changed.

        If there are no meaningful engineering decisions worth questioning, output exactly:

        NO_QUESTIONS

        Otherwise, output only the questions as a numbered list. Do not include explanations, headings, answers, or recommendations.

        File:
        {filename}

        Diff:
        {patch}

        """

  response = client.responses.create(
    model="gpt-5.6-luna",
    input=prompt
  )

  return response.output_text

#V0 mentor questions function:  
'''
def generate_mentor_questionsV0(patch):

  prompt = f""" 
        You are a software engineering mentor.

        Your goal is to help a developer think critically about their
        implementation rather than giving them the solution.

        Review the following code.

        Ask 3 concise questions about meaningful engineering decisions.
        Focus on things such as:
        - data structure choices
        - complexity
        - maintainability
        - error handling
        - design trade-offs

        Do not provide replacement code.
        Do not directly tell the developer what to change.

        Code:
        {patch}
        """

  response = client.responses.create(
    model="gpt-5.6-luna",
    input=prompt
  )

  return response.output_text
'''

if __name__ == "__main__":
  patch = """
  def find_user(users, user_id):
    for user in users:
      if user["id"] == user_id:
        return user
  """
  questions = generate_mentor_questions("example-file", patch)
  print(questions)