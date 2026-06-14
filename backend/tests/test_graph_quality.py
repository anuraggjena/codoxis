from app.services.graph.graph_quality import compute_graph_quality


def test_graph_quality_high_tier():
    q = compute_graph_quality(
        {"total_imports": 10, "resolved_imports": 9},
        {"total_calls": 5, "resolved_calls": 5},
        file_edge_count=12,
    )
    assert q["quality_tier"] == "high"


def test_graph_quality_low_when_no_edges():
    q = compute_graph_quality(
        {"total_imports": 5, "resolved_imports": 1},
        {"total_calls": 0, "resolved_calls": 0},
        file_edge_count=0,
    )
    assert q["quality_tier"] == "low"
    assert q["warnings"]
