import json


def build_refactor_prompt(context: dict, candidates: list, mode: str) -> str:
    instruction = (
        "Explain in simple language for a beginner developer."
        if mode == "beginner"
        else "Use precise technical language for a senior engineer."
    )

    return f"""
You are a senior software architect creating a prioritized refactor plan.

{instruction}

Architecture context:
{json.dumps({
    "architecture_score": context["dashboard"]["version_info"]["architecture_score"],
    "metrics": context["dashboard"]["metrics"],
    "drift": context["drift"],
    "data_quality": context["data_quality"],
}, indent=2)}

Pre-computed refactor candidates (use these as the basis — do not invent files):
{json.dumps(candidates, indent=2)}

Return a JSON object with exactly this shape:
{{
  "summary": "one paragraph overview",
  "recommendations": [
    {{
      "priority": 1,
      "title": "...",
      "category": "...",
      "severity": "high|medium|low",
      "affected_files": ["..."],
      "recommended_action": "...",
      "beginner_explanation": "...",
      "estimated_ahs_impact": "low|medium|high"
    }}
  ]
}}

Keep the same priorities and affected_files from the candidates. Improve the recommended_action and explanations.
Return ONLY valid JSON, no markdown fences.
"""
