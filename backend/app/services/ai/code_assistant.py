from app.services.ai.ai_provider import generate_ai_response
from app.services.ai.code_prompt_builder import build_code_prompt


def analyze_code_snippet(code: str, question: str):

    prompt = build_code_prompt(code, question)

    response = generate_ai_response(prompt)

    return response