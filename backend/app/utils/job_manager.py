import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from app.config.settings import settings

class JobManager:
    def __init__(self):
        self.jobs_file = Path(settings.DATA_DIR) / "jobs.json"
        self._ensure_jobs_file()

    def _ensure_jobs_file(self):
        if not self.jobs_file.exists():
            self.jobs_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.jobs_file, "w") as f:
                json.dump({}, f)

    def _load_jobs(self) -> Dict[str, Any]:
        try:
            with open(self.jobs_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_jobs(self, jobs: Dict[str, Any]):
        with open(self.jobs_file, "w") as f:
            json.dump(jobs, f, indent=2)

    def create_job(self, platform: str, targets: list) -> str:
        job_id = str(uuid.uuid4())
        jobs = self._load_jobs()
        jobs[job_id] = {
            "job_id": job_id,
            "platform": platform,
            "targets": targets,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "result": None,
            "error": None
        }
        self._save_jobs(jobs)
        return job_id

    def update_job(self, job_id: str, status: str, result: Any = None, error: str = None):
        jobs = self._load_jobs()
        if job_id in jobs:
            jobs[job_id]["status"] = status
            jobs[job_id]["updated_at"] = datetime.now().isoformat()
            if result:
                jobs[job_id]["result"] = result
            if error:
                jobs[job_id]["error"] = error
            self._save_jobs(jobs)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        jobs = self._load_jobs()
        return jobs.get(job_id)

job_manager = JobManager()
