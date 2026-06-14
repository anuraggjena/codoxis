# Graph Model

Codoxis builds a **version-scoped dependency graph** for each uploaded repository snapshot.

## Nodes

| Entity | Table | Key fields |
|--------|-------|------------|
| File | `files` | `path`, `language`, `hash` (SHA256), `version_id` |
| Symbol | `symbols` | `name`, `kind`, `file_id` |

## Edges

| `relation_type` | Meaning |
|-----------------|---------|
| `file_import` | Resolved cross-file import (v2 resolver) |
| `call` | Cross-file function/method call |
| `contains` | File → symbol containment |

Edges are stored in `edges` with optional `source_symbol_id` / `target_symbol_id`.

## Metrics

Per-version metrics in `metrics`: circular dependencies, dependency depth, coupling score.

## Graph quality

Stored on `project_versions.graph_quality_json`:

- `resolution_rate_imports` — fraction of parsed imports resolved to files
- `resolution_rate_calls` — fraction of calls resolved cross-file
- `quality_tier` — `high` / `medium` / `low`

## Visualization cap

`build_graph()` caps rendered nodes at `MAX_GRAPH_NODES` (default 200, env-configurable) by centrality.

## Evolution diff

Versions are compared by file path + content hash and edge triplets `(source_path, target_path, relation_type)`.
