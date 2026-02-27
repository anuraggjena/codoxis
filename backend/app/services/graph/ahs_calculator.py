def calculate_ahs(circular_dependencies, coupling_score, dependency_depth):
    """
    Returns Architecture Health Score (0–100)
    """

    # --- Normalize Circular Dependencies ---
    if circular_dependencies == 0:
        cycle_score = 1
    else:
        cycle_score = 1 / (1 + circular_dependencies)

    # --- Normalize Coupling ---
    normalized_coupling = 1 - min(coupling_score / 10, 1)

    # --- Normalize Dependency Depth ---
    normalized_depth = 1 - min(dependency_depth / 15, 1)

    # --- Weighted Score ---
    # Weights sum to 1
    weight_cycle = 0.4
    weight_coupling = 0.35
    weight_depth = 0.25

    final_score = (
        (cycle_score * weight_cycle) +
        (normalized_coupling * weight_coupling) +
        (normalized_depth * weight_depth)
    )

    return round(final_score * 100, 2)