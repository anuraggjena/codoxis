import uuid
from datetime import datetime, timezone

_jobs: dict[str, dict] = {}


def create_job(job_type: str, metadata: dict | None = None) -> str:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "job_id": job_id,
        "type": job_type,
        "status": "pending",
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "result": None,
        "error": None,
    }
    return job_id


def update_job(job_id: str, status: str, result=None, error: str | None = None):
    if job_id in _jobs:
        _jobs[job_id]["status"] = status
        _jobs[job_id]["result"] = result
        _jobs[job_id]["error"] = error


def get_job(job_id: str) -> dict | None:
    return _jobs.get(job_id)
