import logging
from typing import List, Dict, Any
from apify_client import ApifyClient
from app.config.settings import settings
from app.ingestion.base import BaseIngestionService
from app.schemas.ingestion import NormalizedPage, NormalizedPost, NormalizedComment

logger = logging.getLogger(__name__)

class InstagramIngestionService(BaseIngestionService):
    platform = "instagram"

    def __init__(self):
        super().__init__()
        self.client = ApifyClient(settings.APIFY_API_TOKEN) if settings.APIFY_API_TOKEN else None

    def fetch_data(self, targets: List[str], posts_per_page: int = 100, comments_per_post: int = 100, **kwargs) -> List[Dict[str, Any]]:
        if not self.client:
            raise ValueError("Apify API token is not configured")
            
        actor_id = settings.ACTOR_INSTAGRAM_ID
        run_input = {
            "directUrls": [f"https://www.instagram.com/{u}/" for u in targets],
            "resultsType": "details",
            "resultsLimit": posts_per_page,
            "commentsLimit": comments_per_post,
        }
        
        logger.info(f"Running Instagram actor {actor_id}")
        run = self.client.actor(actor_id).call(run_input=run_input)
        return list(self.client.dataset(run["defaultDatasetId"]).iterate_items())

    def normalize_page(self, raw_data: Dict[str, Any]) -> NormalizedPage:
        return NormalizedPage(
            page_id=raw_data.get("id") or "unknown",
            platform=self.platform,
            page_name=raw_data.get("fullName"),
            username=raw_data.get("username"),
            followers_count=raw_data.get("followersCount", 0),
            profile_url=f"https://www.instagram.com/{raw_data.get('username')}/" if raw_data.get("username") else None,
            verified_status=raw_data.get("verified", False),
            metadata=raw_data
        )

    def normalize_post(self, raw_data: Dict[str, Any], page_id: str) -> NormalizedPost:
        return NormalizedPost(
            post_id=raw_data.get("id") or raw_data.get("shortCode") or "unknown",
            page_id=page_id,
            platform=self.platform,
            text=raw_data.get("caption"),
            hashtags=raw_data.get("hashtags", []),
            media_urls=[raw_data.get("displayUrl")] if raw_data.get("displayUrl") else [],
            reactions_count=raw_data.get("likesCount", 0),
            comments_count=raw_data.get("commentsCount", 0),
            shares_count=0, # Instagram doesn't always provide share count
            views_count=raw_data.get("videoViewCount", 0),
            created_time_iso=raw_data.get("timestamp"),
            metadata=raw_data
        )

    def normalize_comment(self, raw_data: Dict[str, Any], post_id: str) -> NormalizedComment:
        return NormalizedComment(
            comment_id=raw_data.get("id") or "unknown",
            post_id=post_id,
            username=raw_data.get("owner", {}).get("username"),
            text=raw_data.get("text"),
            reactions_count=raw_data.get("likesCount", 0),
            created_time_iso=raw_data.get("timestamp"),
            metadata=raw_data
        )

instagram_ingestion_service = InstagramIngestionService()
