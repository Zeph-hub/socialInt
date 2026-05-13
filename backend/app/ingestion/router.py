import logging
from typing import List, Optional
import anthropic
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.ingestion.factory import ingestion_factory
from app.services.normalization_service import normalization_service
from app.repositories.ingestion_repository import ingestion_repository
from app.ai.service import ai_service
from app.utils.job_manager import job_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingestion", tags=["ingestion"])

class IngestionRequest(BaseModel):
    platform: str
    targets: List[str]
    posts_per_page: int = 100
    comments_per_post: int = 100
    debug: Optional[bool] = False
    enrich: Optional[bool] = True

def run_ingestion_task(job_id: str, request: IngestionRequest):
    """Background task to handle the long-running ingestion process."""
    try:
        platform = request.platform.lower()
        service = ingestion_factory.get_service(platform)
        
        if not service:
            job_manager.update_job(job_id, "failed", error=f"Unsupported platform: {platform}")
            return

        job_manager.update_job(job_id, "fetching")
        
        # Fetch raw data using modular service
        raw_data = service.run_with_retry(
            service.fetch_data, 
            request.targets, 
            posts_per_page=request.posts_per_page, 
            comments_per_post=request.comments_per_post
        )
        
        # Persist raw data via repository
        raw_filepath = ingestion_repository.save_raw(platform, raw_data)

        if request.debug:
            job_manager.update_job(job_id, "completed", result={"raw_filepath": raw_filepath})
            return

        job_manager.update_job(job_id, "processing")
        
        # Normalize data via unified normalization service
        standardized_data = normalization_service.normalize_to_standard(platform, raw_data)
        
        # Persist processed data via repository
        processed_filepath = ingestion_repository.save_processed(platform, standardized_data)

        if not request.enrich:
            job_manager.update_job(job_id, "completed", result={
                "raw_filepath": raw_filepath,
                "processed_filepath": processed_filepath
            })
            return

        job_manager.update_job(job_id, "enriching")
        try:
            # AI Analysis step
            enriched_filepath = ai_service.process_data_with_ai(platform, processed_filepath)
            job_manager.update_job(job_id, "completed", result={
                "raw_filepath": raw_filepath,
                "processed_filepath": processed_filepath,
                "enriched_filepath": enriched_filepath
            })
        except anthropic.AuthenticationError:
            job_manager.update_job(job_id, "partial_success", error="Anthropic API key invalid", result={
                "raw_filepath": raw_filepath,
                "processed_filepath": processed_filepath
            })
        except Exception as e:
            logger.error(f"AI Enrichment failed: {str(e)}")
            job_manager.update_job(job_id, "partial_success", error=f"AI Enrichment failed: {str(e)}", result={
                "raw_filepath": raw_filepath,
                "processed_filepath": processed_filepath
            })

    except Exception as e:
        logger.error(f"Ingestion task failed for job {job_id}: {str(e)}")
        job_manager.update_job(job_id, "failed", error=str(e))

@router.post("/")
async def trigger_ingestion(request: IngestionRequest, background_tasks: BackgroundTasks):
    """
    Trigger data ingestion as a background task.
    Returns a job_id to track the status.
    """
    platform = request.platform.lower()
    service = ingestion_factory.get_service(platform)
    if not service:
        raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

    job_id = job_manager.create_job(platform, request.targets)
    background_tasks.add_task(run_ingestion_task, job_id, request)
    
    return {
        "status": "accepted",
        "job_id": job_id,
        "message": f"Ingestion started for {platform} in the background."
    }

@router.get("/status/{job_id}")
def get_ingestion_status(job_id: str):
    """Get the status of an ingestion job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
