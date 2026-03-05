def build_code_prompt(code: str, question: str):

    prompt = f"""
You are a senior software engineer helping a developer understand code.

The developer provided this code snippet:

{code}

Question:
{question}

Your job:

1. Explain what the code does
2. Identify possible issues
3. Suggest improvements
4. If the developer is a beginner, explain concepts clearly
"""

    return prompt