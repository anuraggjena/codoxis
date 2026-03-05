def build_question_prompt(dashboard_data, question):

    metrics = dashboard_data["metrics"]
    summary = dashboard_data["graph_summary"]
    critical_files = dashboard_data["top_critical_files"]

    prompt = f"""
You are an AI software architecture assistant.

The following is architecture analysis of a codebase.

Architecture Score:
{dashboard_data["version_info"]["architecture_score"]}

Metrics:
- Circular Dependencies: {metrics["circular_dependencies"]}
- Dependency Depth: {metrics["dependency_depth"]}
- Coupling Score: {metrics["coupling_score"]}

Graph Summary:
- Total Files: {summary["total_files"]}
- Total Dependencies: {summary["total_dependencies"]}
- Graph Density: {summary["graph_density"]}

High Risk Files:
{critical_files}

A developer asked the following question about the project architecture:

Question:
{question}

Answer the question clearly and give actionable advice.
If the developer is likely a beginner, explain concepts simply in human natural language.
"""

    return prompt