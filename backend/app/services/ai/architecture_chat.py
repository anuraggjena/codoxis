from app.services.ai.question_prompt_builder import build_question_prompt
from app.services.ai.ai_provider import generate_ai_response


def answer_architecture_question(dashboard_data, question):

    prompt = build_question_prompt(dashboard_data, question)

    response = generate_ai_response(prompt)

    return response