from pydantic import BaseModel, Field


class FileChange(BaseModel):
    path: str
    change: str  # added | removed | modified | unchanged
    hash_changed: bool = False


class EdgeChange(BaseModel):
    change: str  # added | removed
    source: str
    target: str
    relation_type: str
    introduces_cycle: bool = False
    cycle_path: list[str] | None = None


class MetricAttribution(BaseModel):
    rank: int
    factor: str
    contribution_estimate: float
    evidence: dict = Field(default_factory=dict)
    evidence_id: str


class EvolutionSummary(BaseModel):
    files_added: int = 0
    files_removed: int = 0
    files_modified: int = 0
    edges_added: int = 0
    edges_removed: int = 0
    ahs_change: float = 0
    coupling_change: float = 0
    cycle_change: int = 0
    depth_change: int = 0


class EvolutionDiff(BaseModel):
    base_version_id: str
    target_version_id: str
    summary: EvolutionSummary
    file_changes: list[FileChange]
    edge_changes: list[EdgeChange]
    metric_attribution: list[MetricAttribution]
    data_quality: str


class RootCauseItem(BaseModel):
    title: str
    severity: str
    evidence_refs: list[str]
    explanation: str
    recommended_action: str


class RootCauseResponse(BaseModel):
    version_id: str
    headline: str
    root_causes: list[RootCauseItem]
    confidence: str
    data_quality_note: str
