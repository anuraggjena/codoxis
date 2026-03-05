import os
from pathlib import Path

from app.models.file import File as FileModel
from app.models.metric import Metric

from app.services.parser.parser import parse_file_content
from app.services.graph.edge_builder import build_edges_for_version
from app.services.graph.import_resolver import resolve_imports
from app.services.graph.cycle_detector import detect_circular_dependencies
from app.services.graph.depth_calculator import calculate_dependency_depth
from app.services.graph.coupling_calculator import calculate_coupling_score
from app.services.graph.ahs_calculator import calculate_ahs
from app.services.graph.drift_detector import detect_architecture_drift

SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".html", ".css"}


def run_repository_analysis(repo_path, version_id, project_id, db):
    """
    Main ingestion pipeline used by both ZIP upload and GitHub import.
    """

    # -------- FILE PARSING --------
    for root, _, files in os.walk(repo_path):
        for filename in files:

            ext = Path(filename).suffix

            if ext not in SUPPORTED_EXTENSIONS:
                continue

            full_path = os.path.join(root, filename)
            relative_path = os.path.relpath(full_path, repo_path)

            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.readlines()

            file_model = FileModel(
                version_id=version_id,
                path=relative_path,
                language=ext.replace(".", ""),
                loc=len(content),
            )

            db.add(file_model)

            parse_file_content(file_model, content, db)

    db.commit()

    # -------- GRAPH BUILDING --------
    build_edges_for_version(version_id, db)

    resolve_imports(version_id, db)

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
    }