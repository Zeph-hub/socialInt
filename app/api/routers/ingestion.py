from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.orchestration.models import PipelineExecution
from app.pipelines.social_pipeline import run_social_pipeline_async
from app.workers.scheduler import worker_scheduler
from app.utils.logger import log

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

class IngestionRequest(BaseModel):
    platform: str
    targets: List[str] # could be usernames, urls, search terms
    posts_per_page: int = 100
    comments_per_post: int = 100
    skip_ai: Optional[bool] = False

@router.post("/")
def trigger_ingestion(request: IngestionRequest):
    """
    Trigger data ingestion and processing pipeline in the background.
    Returns a pipeline_id which can be used to track the status.
    """
    platform = request.platform.lower()
    valid_platforms = ["tiktok", "instagram", "x", "facebook", "youtube", "linkedin"]
    
    if platform not in valid_platforms:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
        
    posts_per_page = max(1, min(request.posts_per_page, 1000))
    comments_per_post = max(0, min(request.comments_per_post, 1000))
    
    # Initialize pipeline execution tracking
    execution = PipelineExecution(
        platform=platform,
        targets=request.targets
    )
    
    try:
        # Enqueue the pipeline job to the background worker scheduler
        job_id = worker_scheduler.enqueue_pipeline(
            run_social_pipeline_async,
            execution=execution,
            skip_ai=request.skip_ai,
            posts_per_page=posts_per_page,
            comments_per_post=comments_per_post
        )
        
        log.info("Pipeline triggered from API", pipeline_id=job_id, platform=platform)
        
        return {
            "status": "accepted",
            "message": f"Pipeline execution started for {platform}",
            "pipeline_id": job_id,
            "tracking_url": f"/api/v1/monitoring/pipelines/{job_id}"
        }
        
    except Exception as e:
        log.error("Failed to trigger pipeline", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to trigger pipeline: {str(e)}")
