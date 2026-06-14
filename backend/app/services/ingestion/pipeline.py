import hashlib
import os
from pathlib import Path

from app.models.file import File as FileModel
from app.models.metric import Metric

from app.services.parser.parser import parse_file_content
from app.services.graph.edge_builder import build_edges_for_version
from app.services.graph.import_resolver_v2 import resolve_imports_v2
from app.services.graph.call_resolver import resolve_calls
from app.services.graph.graph_quality import compute_graph_quality
from app.models.edge import Edge
from app.services.graph.cycle_detector import detect_circular_dependencies
from app.services.graph.depth_calculator import calculate_dependency_depth
from app.services.graph.coupling_calculator import calculate_coupling_score
from app.services.graph.ahs_calculator import calculate_ahs
from app.services.graph.drift_detector import detect_architecture_drift

SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".html", ".css"}
MAX_FILES_PER_REPO = int(os.getenv("MAX_FILES_PER_REPO", "5000"))


def run_repository_analysis(repo_path, version_id, project_id, db):
    """
    Main ingestion pipeline used by both ZIP upload and GitHub import.
    """

    # -------- FILE PARSING --------
    file_count = 0
    for root, _, files in os.walk(repo_path):
        for filename in files:

            ext = Path(filename).suffix

            if ext not in SUPPORTED_EXTENSIONS:
                continue

            file_count += 1
            if file_count > MAX_FILES_PER_REPO:
                raise ValueError(f"Repository exceeds max file limit ({MAX_FILES_PER_REPO})")

            full_path = os.path.join(root, filename)
            relative_path = os.path.relpath(full_path, repo_path)

            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

            file_model = FileModel(
                version_id=version_id,
                path=relative_path,
                language=ext.replace(".", ""),
                loc=len(content.splitlines()),
                hash=content_hash,
            )

            db.add(file_model)
            db.flush()

            parse_file_content(file_model, content, db)

    db.commit()

    # -------- GRAPH BUILDING --------
    build_edges_for_version(version_id, db)

    import_stats = resolve_imports_v2(version_id, db)
    call_stats = resolve_calls(version_id, db)

    file_edge_count = db.query(Edge).filter(
        Edge.version_id == version_id,
        Edge.source_file_id.isnot(None),
        Edge.target_file_id.isnot(None),
    ).count()

    graph_quality = compute_graph_quality(import_stats, call_stats, file_edge_count)

    # -------- METRICS CALCULATION --------
    cycle_count = detect_circular_dependencies(version_id, db)

    depth = calculate_dependency_depth(version_id, db)

    coupling = calculate_coupling_score(version_id, db)

    # -------- STORE METRICS --------
    metric = db.query(Metric).filter(
        Metric.version_id == version_id
    ).first()

    if metric:
        metric.circular_dependencies = cycle_count
        metric.coupling_score = coupling
        metric.dependency_depth = depth
    else:
        metric = Metric(
            version_id=version_id,
            circular_dependencies=cycle_count,
            coupling_score=coupling,
            dependency_depth=depth,
        )
        db.add(metric)

    db.commit()

    # -------- ARCHITECTURE HEALTH SCORE --------
    ahs_score = calculate_ahs(
        circular_dependencies=cycle_count,
        coupling_score=coupling,
        dependency_depth=depth,
    )

    from app.models.project_version import ProjectVersion

    version = db.query(ProjectVersion).filter(
        ProjectVersion.id == version_id
    ).first()

    version.architecture_score = ahs_score
    version.graph_quality_json = graph_quality
    db.commit()

    # -------- DRIFT DETECTION --------
    drift = detect_architecture_drift(project_id, version_id, db)

    return {
        "architecture_score": ahs_score,
        "metrics": {
            "circular_dependencies": cycle_count,
            "dependency_depth": depth,
            "coupling_score": coupling,
        },
        "drift": drift,
        "graph_quality": graph_quality,
    }
