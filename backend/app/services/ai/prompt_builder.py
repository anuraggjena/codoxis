def build_architecture_prompt(dashboard_data, mode="advanced"):

    metrics = dashboard_data["metrics"]
    summary = dashboard_data["graph_summary"]
    critical_files = dashboard_data["top_critical_files"]

    if mode == "beginner":
        instruction = """
Explain the project architecture in simple language.
Assume the developer is new to software architecture.
Avoid technical jargon when possible.
Use simple explanations and examples.
"""
    else:
        instruction = """
Explain the architecture like a senior software architect.
Use precise technical terminology and provide actionable refactoring recommendations.
"""

    prompt = f"""
{instruction}

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

Provide:
1. Architecture summary
2. Key issues detected
3. Suggestions to improve architecture
"""

    return prompt