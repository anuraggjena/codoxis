import json


def build_evidence_prompt(context: dict, mode: str = "advanced") -> str:
    tone = (
        "Explain clearly for a beginner developer."
        if mode == "beginner"
        else "Use senior architect terminology."
    )

    return f"""
You are Codoxis, an architecture intelligence assistant.

{tone}

Use ONLY the evidence below. Cite evidence_id values in your answer like [evidence: risk_1].

Context:
{json.dumps(context, indent=2, default=str)}

Question: {context.get("question", "")}

Provide a helpful, actionable answer grounded in the evidence.
"""
