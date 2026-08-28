from openai import OpenAI

client = OpenAI()

def generate_mentor_questions(patch):

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

if __name__ == "__main__":
  patch = """
  def find_user(users, user_id):
    for user in users:
      if user["id"] == user_id:
        return user
  """
  questions = generate_mentor_questions(patch)
  print(questions)