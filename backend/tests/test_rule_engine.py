from app.services.refactor.rule_engine import prioritize_refactor_candidates


def test_prioritize_returns_sorted_candidates():
    context = {
        "high_risk_files": [
            {"file_path": "a.py", "risk_score": 0.9, "file_id": "id-a"},
            {"file_path": "b.py", "risk_score": 0.5, "file_id": "id-b"},
        ],
        "cycle_paths": [["a.py", "b.py", "a.py"]],
        "centrality": [
            {"file_path": "a.py", "centrality_score": 10},
        ],
        "drift": None,
        "coupling_hotspots": {"a.py": 5},
    }

    candidates = prioritize_refactor_candidates(context, limit=5)

    assert len(candidates) >= 1
    assert candidates[0]["priority"] == 1
    assert "title" in candidates[0]
    assert "evidence" in candidates[0]
