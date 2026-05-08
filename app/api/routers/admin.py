from fastapi import APIRouter

from app.core.config import settings
from app.services.storage_service import storage_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/status")
def get_backend_status():
    platforms = ["tiktok", "instagram", "x", "facebook", "youtube", "linkedin"]
    actor_ids = {
        "tiktok": settings.ACTOR_TIKTOK_ID,
        "instagram": settings.ACTOR_INSTAGRAM_ID,
        "x": settings.ACTOR_X_ID,
        "facebook": settings.ACTOR_FACEBOOK_ID,
        "youtube": settings.ACTOR_YOUTUBE_ID,
        "linkedin": settings.ACTOR_LINKEDIN_ID,
    }

    counts = {}
    for platform in platforms:
        counts[platform] = {
            "raw_files": len(list(storage_service.raw_dir.glob(f"{platform}_*.json"))),
            "processed_files": len(list(storage_service.processed_dir.glob(f"{platform}_processed_*.json"))),
        }

    return {
        "project_name": settings.PROJECT_NAME,
        "api_prefix": settings.API_V1_STR,
        "data_dir": str(storage_service.data_dir.resolve()),
        "raw_dir": str(storage_service.raw_dir.resolve()),
        "processed_dir": str(storage_service.processed_dir.resolve()),
        "apify_configured": bool(settings.APIFY_API_TOKEN.strip()),
        "anthropic_configured": bool(settings.ANTHROPIC_API_KEY.strip()),
        "actor_ids": actor_ids,
        "file_counts": counts,
    }
