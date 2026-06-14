import json


def build_root_cause_prompt(diff: dict, mode: str) -> str:
    tone = (
        "Explain simply for a junior developer."
        if mode == "beginner"
        else "Use precise architectural language for a senior engineer."
    )

    return f"""
You are a principal software architect performing root cause analysis on architecture regression.

{tone}

Evolution diff (ONLY use this evidence):
{json.dumps(diff, indent=2)}

Return JSON:
{{
  "headline": "one sentence summary",
  "root_causes": [
    {{
      "title": "...",
      "severity": "high|medium|low",
      "evidence_refs": ["attribution_1"],
      "explanation": "...",
      "recommended_action": "..."
    }}
  ]
}}

Do NOT invent files or edges not present in the diff. Return ONLY valid JSON.
"""
