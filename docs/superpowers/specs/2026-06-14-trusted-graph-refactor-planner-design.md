# Trusted Graph Foundation + AI Refactor Planner — Design Spec

**Date:** 2026-06-14  
**Status:** Approved  
**Author:** Architecture review (brainstorming session)

---

## 1. Problem Statement

Codoxis has a broad backend API surface (ingestion, graph analysis, metrics, AI) but the core analysis pipeline has correctness bugs that undermine all downstream intelligence:

1. **Parse bug:** `pipeline.py` passes `f.readlines()` (a list) to `parse_file_content()` which expects a `str` and calls `bytes(content, "utf8")`.
2. **Edge schema mismatch:** `Edge` model requires four non-null FK columns; `edge_builder.py` sets only symbol IDs and `import_resolver.py` sets only file IDs.
3. **Graph loader gap:** `graph_loader.py` only loads file-level edges, so symbol-only edges do not feed metrics or AI context even if they persisted.

Building the planned **AI Refactor Planner** on this foundation would produce confident but unreliable recommendations. This phase fixes the data layer and ships Refactor Planner as the acceptance test for trustworthy architecture intelligence.

---

## 2. Goals

| Goal | Success Criteria |
|------|------------------|
| Trustworthy ingestion | Upload a test repo → files, symbols, edges, metrics persist correctly |
| Correct graph metrics | Cycles, coupling, depth computed from file-level edges |
| Secured API surface | All `/ai/*` and `/analysis/*` routes require JWT + project ownership |
| AI Refactor Planner | `GET /ai/refactor-plan/{version_id}` returns prioritized, evidence-backed recommendations |
| Test foundation | pytest suite covers pipeline, edges, auth, refactor planner response shape |

---

## 3. Non-Goals (Deferred)

- GitHub OAuth → JWT user linking
- Alembic migrations (initialize after Edge model is finalized)
- Frontend MVP
- Background job queue for large repos
- Cross-file call resolution
- Rate limiting middleware (document limits; simple cap in refactor planner)
- Betweenness centrality

---

## 4. Architecture

### 4.1 Layered Changes

```
┌─────────────────────────────────────────────────────────┐
│  routers/ai.py  — GET /ai/refactor-plan/{version_id}   │
│  auth/version_access.py — ownership dependency          │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│  services/refactor/                                     │
│    context_builder.py  — aggregate graph intelligence   │
│    rule_engine.py      — deterministic prioritization   │
│    refactor_planner.py — orchestrate rules → AI → output│
│    schemas.py          — Pydantic response models       │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│  services/ai/refactor_prompt_builder.py                 │
│  services/ai/ai_provider.py (hardened)                  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│  Existing: dashboard, risk_analyzer, cycle_detector,    │
│  centrality, drift, impact, graph_loader                │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│  Fixed: pipeline.py, edge_builder.py, import_resolver.py│
│  Fixed: models/edge.py (nullable symbol FKs)            │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Edge Model Decision

Make `source_symbol_id` and `target_symbol_id` **nullable** on `Edge`. Rationale:

- File-level import edges (`file_import`) have no meaningful symbol targets today.
- Symbol-level call edges can populate file FKs from the symbol's `file_id`.
- Avoids placeholder self-referencing symbol edges for imports.
- `graph_loader.py` already filters on file FKs — this aligns model with usage.

### 4.3 Auth Pattern

New dependency `get_version_for_user(version_id, current_user, db)`:

1. Load `ProjectVersion` by `version_id` → 404 if missing
2. Load `Project` by `version.project_id` → 404 if missing
3. Verify `project.user_id == current_user.id` → 403 if not
4. Return `(version, project)` tuple

Applied to all version-scoped and project-scoped analysis/AI routes.

---

## 5. API Specification

### 5.1 New Endpoint

```
GET /ai/refactor-plan/{version_id}
```

**Authentication:** Required (Bearer JWT)

**Authorization:** User must own the project containing `version_id`

**Query Parameters:**

| Parameter | Type | Default | Validation |
|-----------|------|---------|------------|
| `mode` | string | `advanced` | `beginner` or `advanced` |
| `limit` | integer | `10` | 1–20 inclusive |

**Response 200:**

```json
{
  "version_id": "550e8400-e29b-41d4-a716-446655440000",
  "mode": "advanced",
  "architecture_score": 72.5,
  "data_quality": "high",
  "summary": "3 high-priority structural issues detected in your architecture.",
  "recommendations": [
    {
      "priority": 1,
      "title": "Break circular dependency between parser and graph modules",
      "category": "circular_dependency",
      "severity": "high",
      "affected_files": ["services/parser/parser.py", "services/graph/edge_builder.py"],
      "evidence": {
        "cycle_path": ["services/parser/parser.py", "services/graph/edge_builder.py", "services/parser/parser.py"],
        "centrality_scores": {"services/parser/parser.py": 0.82},
        "impact_radius": 14,
        "metrics_contribution": {"circular_dependencies": 1, "coupling": 0.3}
      },
      "recommended_action": "Introduce an interface module to decouple parser from graph edge building.",
      "beginner_explanation": "Two files depend on each other in a loop, which makes changes risky.",
      "estimated_ahs_impact": "medium"
    }
  ],
  "ai_enhanced": true,
  "generated_at": "2026-06-14T12:00:00Z"
}
```

**Error Responses:**

| Status | Body | Condition |
|--------|------|-----------|
| 401 | `{"detail": "Invalid token"}` | Missing or invalid JWT |
| 403 | `{"detail": "Access denied"}` | User does not own project |
| 404 | `{"detail": "Version not found"}` | Invalid version_id |
| 422 | FastAPI validation error | Invalid mode or limit |
| 503 | `{"detail": "AI service unavailable"}` | OpenRouter failure after rule-only fallback attempted |

### 5.2 Modified Route Protection

All endpoints in `routers/analysis.py` and `routers/ai.py` gain `current_user: User = Depends(get_current_user)` and version/project ownership checks where applicable.

Timeline endpoints (`/analysis/timeline/{project_id}`) verify project ownership via `project.user_id`.

---

## 6. Service Design

### 6.1 `build_refactor_context(version_id, db) → dict`

Aggregates:

| Source | Function | Data |
|--------|----------|------|
| Dashboard | `build_dashboard()` | metrics, graph summary, drift, top critical files |
| High risk | `detect_high_risk_files()` | top 10 risk-scored files |
| Cycles | `find_cycle_paths()` (new) | list of file-path cycles |
| Centrality | `calculate_file_centrality()` | ranked files |
| Impact | `analyze_refactor_impact()` | for top 3 critical file IDs |

Returns structured dict used by rule engine and prompt builder.

### 6.2 `prioritize_refactor_candidates(context) → list[dict]`

Deterministic scoring (no AI):

| Signal | Weight |
|--------|--------|
| Circular dependency involvement | 0.30 |
| High-risk score | 0.25 |
| Centrality (normalized) | 0.20 |
| Drift regression (if prior version) | 0.15 |
| Coupling hotspot (outgoing deps) | 0.10 |

Each candidate includes: `category`, `severity`, `affected_files`, `evidence`, `score`.

Categories: `circular_dependency`, `high_coupling`, `high_centrality`, `drift_regression`, `large_file`.

### 6.3 `generate_refactor_plan(version_id, db, mode, limit) → RefactorPlanResponse`

1. Build context
2. Run rule engine → top `limit` candidates
3. Build AI prompt with candidates + context
4. Call `generate_ai_response()` with `max_tokens=2000`
5. Parse AI response as JSON (structured output in prompt)
6. Merge AI narrative with deterministic evidence
7. On AI failure: return rule-only plan with `ai_enhanced: false`

### 6.4 `find_cycle_paths(version_id, db) → list[list[str]]`

Extend `cycle_detector.py`:

- DFS with path tracking
- Return up to 10 unique cycle paths as lists of file paths (not IDs)
- Deduplicate rotated cycles

---

## 7. Data Flow

```
Client: GET /ai/refactor-plan/{version_id}?mode=beginner&limit=5
  │
  ├─ JWT validation (get_current_user)
  ├─ Ownership check (get_version_for_user)
  │
  ├─ build_refactor_context(version_id, db)
  │     ├─ build_dashboard()
  │     ├─ detect_high_risk_files()
  │     ├─ find_cycle_paths()
  │     ├─ calculate_file_centrality()
  │     └─ analyze_refactor_impact() × 3
  │
  ├─ prioritize_refactor_candidates(context)
  │
  ├─ build_refactor_prompt(context, candidates, mode)
  │
  ├─ generate_ai_response(prompt)  [or skip on failure]
  │
  └─ RefactorPlanResponse
```

---

## 8. Foundation Fixes

### 8.1 Pipeline Content Fix

```python
# pipeline.py — change readlines() to read()
with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()
file_model.loc = len(content.splitlines())
```

### 8.2 Edge Builder Fix

- Replace raw SQL with SQLAlchemy ORM query
- For call edges: set `source_file_id` and `target_file_id` from symbols' `file_id`
- Set `source_symbol_id` = function.id, `target_symbol_id` = call.id
- Remove import placeholder edges (handled by `import_resolver`)

### 8.3 Import Resolver Fix

- `create_file_edge()` sets only file FKs; symbol FKs remain `None`
- Requires nullable symbol columns on Edge model

### 8.4 CORS

```python
# main.py
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 8.5 Security

- Remove hardcoded `SECRET_KEY` fallback; require env var
- ZIP: 50 MB max size, zip-slip path validation before `extractall`
- GitHub URL: allow only `https://github.com/` prefix

---

## 9. Pydantic Schemas

```python
# services/refactor/schemas.py

class RefactorEvidence(BaseModel):
    cycle_path: list[str] | None = None
    centrality_scores: dict[str, float] = {}
    impact_radius: int | None = None
    metrics_contribution: dict[str, float] = {}

class RefactorRecommendation(BaseModel):
    priority: int
    title: str
    category: str
    severity: str  # low | medium | high
    affected_files: list[str]
    evidence: RefactorEvidence
    recommended_action: str
    beginner_explanation: str
    estimated_ahs_impact: str  # low | medium | high

class RefactorPlanResponse(BaseModel):
    version_id: str
    mode: str
    architecture_score: float | None
    data_quality: str  # low | medium | high
    summary: str
    recommendations: list[RefactorRecommendation]
    ai_enhanced: bool
    generated_at: datetime
```

---

## 10. Edge Cases

| Scenario | Behavior |
|----------|----------|
| No file edges | `data_quality: "low"`; recommendations from metrics only |
| No cycles | Skip `circular_dependency` category |
| Single-file repo | Recommend modularization if LOC > 300 |
| AI timeout/error | Rule-only plan, `ai_enhanced: false` |
| Version with no metrics | 404 "Analysis incomplete" |
| Repo > 500 files | Cap context to top 20 risk files |

---

## 11. Testing Strategy

| Test File | Coverage |
|-----------|----------|
| `tests/test_pipeline.py` | File/symbol/metric persistence after `run_repository_analysis` |
| `tests/test_edges.py` | File-level import edges and call edges with correct FKs |
| `tests/test_cycle_paths.py` | `find_cycle_paths` returns valid paths |
| `tests/test_auth.py` | Register, login, 401 on protected routes |
| `tests/test_refactor_planner.py` | Rule engine scoring, response schema, auth on endpoint |
| `tests/test_version_access.py` | 403 for wrong user |

Test fixture: minimal Python repo with circular import created in `tests/fixtures/sample_repo/`.

---

## 12. Rollout

1. **Foundation fixes** — verify pipeline on Codoxis self-ingestion
2. **Auth + CORS** — enable frontend integration
3. **Refactor planner** — internal alpha with 3 sample repos
4. **Document** — update CODOXIS.md with new endpoint

---

## 13. Dependencies

| Dependency | Purpose |
|------------|---------|
| Existing dashboard, risk, centrality, drift, impact services | Context for refactor planner |
| OpenRouter API | AI narrative generation |
| pytest, httpx | Test infrastructure |
| No new runtime packages required beyond test deps |

---

## 14. Open Questions (Resolved)

| Question | Decision |
|----------|----------|
| Nullable symbol FKs vs populate all FKs? | Nullable symbol FKs — simpler, matches graph_loader usage |
| AI-only vs hybrid? | Hybrid: deterministic rules first, AI narrates and refines |
| Separate refactor router? | No — add to existing `routers/ai.py` per CODOXIS.md |
