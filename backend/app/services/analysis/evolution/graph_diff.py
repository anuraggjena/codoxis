from app.models.file import File
from app.models.edge import Edge
from app.models.metric import Metric
from app.models.project_version import ProjectVersion
from app.services.analysis.evolution.schemas import (
    EdgeChange,
    EvolutionDiff,
    EvolutionSummary,
    FileChange,
    MetricAttribution,
)
from app.services.graph.cycle_detector import find_cycle_paths


def _norm(path: str) -> str:
    return path.replace("\\", "/")


def _file_map(version_id, db) -> dict[str, File]:
    return {_norm(f.path): f for f in db.query(File).filter(File.version_id == version_id).all()}


def _edge_set(version_id, db, path_to_file: dict[str, File]) -> set[tuple[str, str, str]]:
    id_to_path = {f.id: p for p, f in path_to_file.items()}
    edges = db.query(Edge).filter(
        Edge.version_id == version_id,
        Edge.source_file_id.isnot(None),
        Edge.target_file_id.isnot(None),
    ).all()
    result = set()
    for e in edges:
        sp = id_to_path.get(e.source_file_id)
        tp = id_to_path.get(e.target_file_id)
        if sp and tp:
            result.add((sp, tp, e.relation_type))
    return result


def build_evolution_diff(target: ProjectVersion, base: ProjectVersion, db) -> EvolutionDiff:
    base_files = _file_map(base.id, db)
    target_files = _file_map(target.id, db)

    file_changes: list[FileChange] = []
    all_paths = set(base_files) | set(target_files)

    for path in sorted(all_paths):
        b = base_files.get(path)
        t = target_files.get(path)
        if b and not t:
            file_changes.append(FileChange(path=path, change="removed"))
        elif t and not b:
            file_changes.append(FileChange(path=path, change="added"))
        elif b and t and b.hash != t.hash:
            file_changes.append(FileChange(path=path, change="modified", hash_changed=True))

    base_edges = _edge_set(base.id, db, base_files)
    target_edges = _edge_set(target.id, db, target_files)

    cycles = find_cycle_paths(target.id, db)
    cycle_edge_pairs = set()
    for cyc in cycles:
        for i in range(len(cyc) - 1):
            cycle_edge_pairs.add((_norm(cyc[i]), _norm(cyc[i + 1])))

    edge_changes: list[EdgeChange] = []
    for sp, tp, rel in sorted(target_edges - base_edges):
        introduces = (_norm(sp), _norm(tp)) in cycle_edge_pairs or any(
            _norm(sp) in c and _norm(tp) in c for c in cycles
        )
        cpath = next((c for c in cycles if _norm(sp) in map(_norm, c) and _norm(tp) in map(_norm, c)), None)
        edge_changes.append(EdgeChange(
            change="added",
            source=sp,
            target=tp,
            relation_type=rel,
            introduces_cycle=introduces,
            cycle_path=cpath,
        ))

    for sp, tp, rel in sorted(base_edges - target_edges):
        edge_changes.append(EdgeChange(change="removed", source=sp, target=tp, relation_type=rel))

    m_base = db.query(Metric).filter(Metric.version_id == base.id).first()
    m_target = db.query(Metric).filter(Metric.version_id == target.id).first()

    summary = EvolutionSummary(
        files_added=sum(1 for f in file_changes if f.change == "added"),
        files_removed=sum(1 for f in file_changes if f.change == "removed"),
        files_modified=sum(1 for f in file_changes if f.change == "modified"),
        edges_added=sum(1 for e in edge_changes if e.change == "added"),
        edges_removed=sum(1 for e in edge_changes if e.change == "removed"),
        ahs_change=(target.architecture_score or 0) - (base.architecture_score or 0),
        coupling_change=(m_target.coupling_score or 0) - (m_base.coupling_score or 0) if m_target and m_base else 0,
        cycle_change=(m_target.circular_dependencies or 0) - (m_base.circular_dependencies or 0) if m_target and m_base else 0,
        depth_change=(m_target.dependency_depth or 0) - (m_base.dependency_depth or 0) if m_target and m_base else 0,
    )

    attribution = _build_attribution(summary, edge_changes)

    data_quality = (target.graph_quality_json or {}).get("quality_tier", "low")

    return EvolutionDiff(
        base_version_id=str(base.id),
        target_version_id=str(target.id),
        summary=summary,
        file_changes=file_changes,
        edge_changes=edge_changes,
        metric_attribution=attribution,
        data_quality=data_quality,
    )


def _build_attribution(summary: EvolutionSummary, edge_changes: list[EdgeChange]) -> list[MetricAttribution]:
    scored: list[tuple[float, MetricAttribution]] = []

    cycle_edges = [e for e in edge_changes if e.change == "added" and e.introduces_cycle]
    if cycle_edges:
        e = cycle_edges[0]
        scored.append((0.45, MetricAttribution(
            rank=0,
            factor="new_circular_dependency",
            contribution_estimate=0.45,
            evidence={"cycle_path": e.cycle_path, "edge": f"{e.source} -> {e.target}"},
            evidence_id="attribution_cycle",
        )))

    if summary.edges_added > 0:
        scored.append((0.25, MetricAttribution(
            rank=0,
            factor="coupling_increase",
            contribution_estimate=0.25,
            evidence={"edges_added": summary.edges_added, "coupling_change": summary.coupling_change},
            evidence_id="attribution_coupling",
        )))

    if summary.files_added > 0:
        scored.append((0.15, MetricAttribution(
            rank=0,
            factor="new_files",
            contribution_estimate=0.15,
            evidence={"files_added": summary.files_added},
            evidence_id="attribution_files",
        )))

    if summary.ahs_change < 0 and not scored:
        scored.append((0.3, MetricAttribution(
            rank=0,
            factor="architecture_regression",
            contribution_estimate=0.3,
            evidence={"ahs_change": summary.ahs_change},
            evidence_id="attribution_ahs",
        )))

    scored.sort(key=lambda x: x[0], reverse=True)
    result = []
    for i, (_, item) in enumerate(scored[:5]):
        item.rank = i + 1
        result.append(item)
    return result
