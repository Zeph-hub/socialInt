from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.storage.manager import storage

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/health")
def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "service": "socialInt"}

@router.get("/ready")
def readiness_check():
    """Readiness check for load balancers."""
    return {"status": "ready"}

@router.get("/metrics")
def get_metrics():
    """Get basic metrics about the pipeline system."""
    pipelines = storage.list_pipelines()
    completed = [p for p in pipelines if p.get("status") == "completed"]
    failed = [p for p in pipelines if p.get("status") == "failed"]
    running = [p for p in pipelines if p.get("status") == "running"]
    
    total_records = sum(p.get("records_processed", 0) for p in completed)
    
    return {
        "total_pipelines": len(pipelines),
        "completed": len(completed),
        "failed": len(failed),
        "running": len(running),
        "total_records_processed": total_records
    }

@router.get("/pipelines", response_model=List[Dict[str, Any]])
def list_pipelines(limit: int = 50):
    """List all recent pipeline executions."""
    pipelines = storage.list_pipelines()
    # Sort by started_at descending
    pipelines.sort(key=lambda x: x.get("started_at", ""), reverse=True)
    return pipelines[:limit]

@router.get("/pipelines/{pipeline_id}")
def get_pipeline(pipeline_id: str):
    """Get details of a specific pipeline execution."""
    pipeline = storage.load_pipeline_metadata(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline
