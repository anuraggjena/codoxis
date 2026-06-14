from datetime import datetime

from pydantic import BaseModel, Field


class RefactorEvidence(BaseModel):
    cycle_path: list[str] | None = None
    centrality_scores: dict[str, float] = Field(default_factory=dict)
    impact_radius: int | None = None
    metrics_contribution: dict[str, float] = Field(default_factory=dict)


class RefactorRecommendation(BaseModel):
    priority: int
    title: str
    category: str
    severity: str
    affected_files: list[str]
    evidence: RefactorEvidence
    recommended_action: str
    beginner_explanation: str
    estimated_ahs_impact: str


class RefactorPlanResponse(BaseModel):
    version_id: str
    mode: str
    architecture_score: float | None
    data_quality: str
    summary: str
    recommendations: list[RefactorRecommendation]
    ai_enhanced: bool
    generated_at: datetime
