from functools import lru_cache

from app.services.dashboard.dashboard_service import build_dashboard
from app.services.graph.graph_builder import build_graph


@lru_cache(maxsize=128)
def _dashboard_key(version_id: str):
    return version_id


def get_cached_dashboard(version_id, db):
    return build_dashboard(version_id, db)


def get_cached_graph(version_id, db):
    return build_graph(version_id, db)


def invalidate_version_cache(version_id):
    _dashboard_key.cache_clear()
