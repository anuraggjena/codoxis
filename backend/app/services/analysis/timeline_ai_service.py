from app.services.analysis.timeline_service import get_architecture_timeline
from app.services.ai.ai_provider import generate_ai_response


def build_timeline_prompt(timeline):

    prompt = f"""
You are a senior software architect.

Below is architecture evolution data for a software project.

Timeline Data:
{timeline}

Your job:

1. Explain how the architecture changed across versions
2. Identify when architecture quality improved or degraded
3. Explain the likely causes (coupling, dependency depth, circular dependencies)
4. Provide suggestions for improving architecture

Explain clearly so both beginner and experienced developers can understand.
"""

    return prompt


def explain_architecture_timeline(project_id, db):

    timeline = get_architecture_timeline(project_id, db)

    prompt = build_timeline_prompt(timeline)

    explanation = generate_ai_response(prompt)

    return {
        "timeline": timeline,
        "ai_explanation": explanation
    }