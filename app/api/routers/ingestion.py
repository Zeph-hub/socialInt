from typing import List, Optional
import anthropic
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.apify_service import apify_service
from app.services.processing_service import processing_service
from app.services.ai_service import ai_service

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

class IngestionRequest(BaseModel):
    platform: str
    targets: List[str] # could be usernames, urls, search terms
    posts_per_page: int = 100
    comments_per_post: int = 100
    debug: Optional[bool] = False  # Skip processing/enrichment for debugging
    enrich: Optional[bool] = True  # Set false to skip Claude AI analysis only

@router.post("/")
def trigger_ingestion(request: IngestionRequest):
    """
    Trigger data ingestion from Apify for a specific platform.
    
    Set debug=true to skip processing/enrichment and get raw data directly,
    allowing you to compare with the Apify dashboard output.
    """
    try:
        platform = request.platform.lower()
        posts_per_page = max(1, min(request.posts_per_page, 1000))
        comments_per_post = max(0, min(request.comments_per_post, 1000))
        
        # Fetch raw data from Apify
        if platform == "tiktok":
            filepath = apify_service.fetch_tiktok_data(request.targets, posts_per_page, comments_per_post)
        elif platform == "instagram":
            filepath = apify_service.fetch_instagram_data(request.targets, posts_per_page, comments_per_post)
        elif platform == "x":
            filepath = apify_service.fetch_x_data(request.targets, posts_per_page, comments_per_post)
        elif platform == "facebook":
            filepath = apify_service.fetch_facebook_data(request.targets, posts_per_page, comments_per_post)
        elif platform == "youtube":
            filepath = apify_service.fetch_youtube_data(request.targets, posts_per_page, comments_per_post)
        elif platform == "linkedin":
            filepath = apify_service.fetch_linkedin_data(request.targets, posts_per_page, comments_per_post)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")
        
        # Return early in debug mode
        if request.debug:
            return {
                "status": "success",
                "mode": "debug",
                "message": f"Raw data fetched for {platform} (no processing/enrichment)",
                "filepath": filepath
            }
        
        # Processing step
        processed_filepath = processing_service.process_and_save_data(platform, filepath)
        
        if not request.enrich:
            return {
                "status": "success",
                "mode": "no_ai",
                "message": f"Data fetched and processed for {platform} (AI enrichment skipped)",
                "filepaths": {
                    "raw": filepath,
                    "processed": processed_filepath,
                    "enriched": None
                }
            }
        
        try:
            # AI Analysis step
            enriched_filepath = ai_service.process_data_with_ai(platform, processed_filepath)
        except anthropic.AuthenticationError:
            return {
                "status": "partial_success",
                "message": (
                    f"Data fetched and processed for {platform}, but AI enrichment was skipped "
                    "because ANTHROPIC_API_KEY is invalid."
                ),
                "filepaths": {
                    "raw": filepath,
                    "processed": processed_filepath,
                    "enriched": None
                },
                "warning": "Update ANTHROPIC_API_KEY in .env with a valid Anthropic Console API key, then restart the API server."
            }
        
        return {
            "status": "success", 
            "message": f"Data fetched, processed, and enriched for {platform}", 
            "filepaths": {
                "raw": filepath,
                "processed": processed_filepath,
                "enriched": enriched_filepath
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
