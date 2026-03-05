from app.services.ai.prompt_builder import build_architecture_prompt
from app.services.ai.ai_provider import generate_ai_response


def generate_architecture_analysis(dashboard_data, mode="advanced"):

    prompt = build_architecture_prompt(dashboard_data, mode)

    ai_response = generate_ai_response(prompt)

    return ai_response