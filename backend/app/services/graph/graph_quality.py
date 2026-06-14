def compute_graph_quality(
    import_stats: dict,
    call_stats: dict,
    file_edge_count: int,
) -> dict:
    total_imports = import_stats.get("total_imports", 0)
    resolved_imports = import_stats.get("resolved_imports", 0)
    total_calls = call_stats.get("total_calls", 0)
    resolved_calls = call_stats.get("resolved_calls", 0)

    import_rate = (resolved_imports / total_imports) if total_imports else 1.0
    call_rate = (resolved_calls / total_calls) if total_calls else 1.0

    combined = (import_rate * 0.7) + (call_rate * 0.3)

    if combined >= 0.85:
        tier = "high"
    elif combined >= 0.6:
        tier = "medium"
    else:
        tier = "low"

    warnings = []
    if total_imports and import_rate < 0.85:
        warnings.append(f"{total_imports - resolved_imports} unresolved imports")
    if total_calls and call_rate < 0.6:
        warnings.append(f"{total_calls - resolved_calls} unresolved call sites")
    if file_edge_count == 0:
        warnings.append("No file-level dependency edges detected")

    return {
        "resolution_rate_imports": round(import_rate, 4),
        "resolution_rate_calls": round(call_rate, 4),
        "file_graph_edge_count": file_edge_count,
        "quality_tier": tier,
        "warnings": warnings,
    }
