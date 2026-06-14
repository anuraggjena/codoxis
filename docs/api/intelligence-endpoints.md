# Intelligence API Endpoints

Base URL: `/` (FastAPI). All routes except auth require `Authorization: Bearer <JWT>`.

## Analysis

| Method | Path | Description |
|--------|------|-------------|
| GET | `/analysis/dashboard/{version_id}` | Metrics, drift, graph quality, critical files |
| GET | `/analysis/graph/{version_id}` | Force-graph JSON (capped nodes) |
| GET | `/analysis/graph-quality/{version_id}` | Import/call resolution rates |
| GET | `/analysis/evolution/{version_id}` | Structural diff vs previous version |
| GET | `/analysis/compare/{v1}/{v2}` | Metric comparison between two versions |
| GET | `/analysis/dependency-path/{version_id}?from=&to=` | Shortest import paths |
| GET | `/analysis/clusters/{version_id}` | Module clusters |
| GET | `/analysis/boundaries/{version_id}` | Layer boundary violations |
| GET | `/analysis/debt/{version_id}` | Per-file technical debt scores |
| GET | `/analysis/debt-trajectory/{project_id}` | Debt trend across versions |
| GET | `/analysis/heatmap/{version_id}` | Risk × centrality heat scores |
| GET | `/analysis/commit-impact/{version_id}` | Commit-scoped impact (git versions) |
| GET | `/analysis/timeline/{project_id}` | Version history with AHS deltas |

## AI

| Method | Path | Description |
|--------|------|-------------|
| GET | `/ai/refactor-plan/{version_id}` | Rule + optional AI refactor plan |
| GET | `/ai/root-cause/{version_id}` | Evolution-backed root cause narrative |
| POST | `/ai/copilot/ask` | Evidence-backed Q&A with citations |
| GET | `/ai/copilot/suggestions/{version_id}` | Suggested questions |
| GET | `/ai/ask/{version_id}` | Simple architecture Q&A |

## Ingestion

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ingestion/upload/{project_id}` | Sync ZIP upload + analysis |
| POST | `/ingestion/upload-async/{project_id}` | Background ZIP job |
| GET | `/ingestion/status/{job_id}` | Poll async job status |
| POST | `/ingestion/github/{project_id}` | Clone latest GitHub snapshot |
| POST | `/ingestion/github/commits/{project_id}` | Import last N commits |

Rate limits apply to `/ai/*` routes (see `AIRateLimitMiddleware`).
