import uuid
from datetime import datetime, timezone

from git import Repo

from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.services.ingestion.pipeline import run_repository_analysis

MAX_COMMITS = 5


def import_commits(project_id, repo_url: str, db, max_commits: int = MAX_COMMITS, github_token: str | None = None) -> list[dict]:
    import tempfile
    import shutil

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return []

    temp_dir = tempfile.mkdtemp()
    results = []
    clone_url = repo_url
    if github_token and repo_url.startswith("https://github.com/"):
        clone_url = repo_url.replace("https://", f"https://{github_token}@", 1)
    try:
        repo = Repo.clone_from(clone_url, temp_dir, depth=max_commits)
        commits = list(repo.iter_commits(max_count=max_commits))

        for commit in reversed(commits):
            repo.git.checkout(commit.hexsha)
            version_count = db.query(ProjectVersion).filter(
                ProjectVersion.project_id == project_id
            ).count()

            version = ProjectVersion(
                project_id=project_id,
                version_number=version_count + 1,
                commit_sha=commit.hexsha,
                commit_message=(commit.message or "")[:500],
                source_type="github_commit",
                ingestion_status="processing",
            )
            db.add(version)
            db.commit()
            db.refresh(version)

            try:
                analysis = run_repository_analysis(temp_dir, version.id, project.id, db)
                version.ingestion_status = "completed"
                db.commit()
                results.append({
                    "version_id": str(version.id),
                    "commit_sha": commit.hexsha,
                    "architecture_score": analysis.get("architecture_score"),
                })
            except Exception:
                version.ingestion_status = "failed"
                db.commit()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    return results
