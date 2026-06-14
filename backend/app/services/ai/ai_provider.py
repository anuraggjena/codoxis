import logging
from openai import OpenAI, APIError
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

MODEL = "openai/gpt-5.3-codex"


def generate_ai_response(prompt: str, max_tokens: int = 1200) -> str | None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY not set")
        return None

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior software architect helping developers understand their system architecture.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        return completion.choices[0].message.content
    except APIError as e:
        logger.error("AI provider error: %s", e)
        return None
