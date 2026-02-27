from app.models.project_version import ProjectVersion
from app.models.metric import Metric
from app.models.file import File
from app.models.edge import Edge


def compare_versions(version_id_1, version_id_2, db):
    v1 = db.query(ProjectVersion).filter(
        ProjectVersion.id == version_id_1
    ).first()

    v2 = db.query(ProjectVersion).filter(
        ProjectVersion.id == version_id_2
    ).first()

    if not v1 or not v2:
        return None

    m1 = db.query(Metric).filter(Metric.version_id == v1.id).first()
    m2 = db.query(Metric).filter(Metric.version_id == v2.id).first()

    files_v1 = db.query(File).filter(File.version_id == v1.id).count()
    files_v2 = db.query(File).filter(File.version_id == v2.id).count()

    edges_v1 = db.query(Edge).filter(
        Edge.version_id == v1.id,
        Edge.source_file_id.isnot(None),
        Edge.target_file_id.isnot(None)
    ).count()

    edges_v2 = db.query(Edge).filter(
        Edge.version_id == v2.id,
        Edge.source_file_id.isnot(None),
        Edge.target_file_id.isnot(None)
    ).count()

    comparison = {
        "version_1": {
            "id": v1.id,
            "number": v1.version_number,
            "architecture_score": v1.architecture_score
        },
        "version_2": {
            "id": v2.id,
            "number": v2.version_number,
            "architecture_score": v2.architecture_score
        },
        "delta": {
            "ahs_change": (v2.architecture_score or 0) - (v1.architecture_score or 0),
            "circular_dependency_change": (m2.circular_dependencies if m2 else 0)
                                           - (m1.circular_dependencies if m1 else 0),
            "coupling_change": (m2.coupling_score if m2 else 0)
                               - (m1.coupling_score if m1 else 0),
            "depth_change": (m2.dependency_depth if m2 else 0)
                            - (m1.dependency_depth if m1 else 0),
            "file_growth": files_v2 - files_v1,
            "dependency_growth": edges_v2 - edges_v1,
        }
    }

    return comparison