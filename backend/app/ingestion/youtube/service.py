import logging
from typing import List, Dict, Any
from apify_client import ApifyClient
from app.config.settings import settings
from app.ingestion.base import BaseIngestionService
from app.schemas.ingestion import NormalizedPage, NormalizedPost, NormalizedComment

logger = logging.getLogger(__name__)

class YouTubeIngestionService(BaseIngestionService):
    platform = "youtube"

    def __init__(self):
        super().__init__()
        self.client = ApifyClient(settings.APIFY_API_TOKEN) if settings.APIFY_API_TOKEN else None

    def fetch_data(self, targets: List[str], posts_per_page: int = 100, comments_per_post: int = 100, **kwargs) -> List[Dict[str, Any]]:
        if not self.client:
            raise ValueError("Apify API token is not configured")
            
        actor_id = settings.ACTOR_YOUTUBE_ID
        run_input = {
            "startUrls": [{"url": c} for c in targets],
            "maxResults": posts_per_page,
            "maxComments": comments_per_post,
        }
        
        logger.info(f"Running YouTube actor {actor_id}")
        run = self.client.actor(actor_id).call(run_input=run_input)
        return list(self.client.dataset(run["defaultDatasetId"]).iterate_items())

    def normalize_page(self, raw_data: Dict[str, Any]) -> NormalizedPage:
        return NormalizedPage(
            page_id=raw_data.get("id") or "unknown",
            platform=self.platform,
            page_name=raw_data.get("title"),
            username=raw_data.get("id"),
            followers_count=raw_data.get("numberOfSubscribers", 0),
            profile_url=raw_data.get("url"),
            metadata=raw_data
        )

    def normalize_post(self, raw_data: Dict[str, Any], page_id: str) -> NormalizedPost:
        return NormalizedPost(
            post_id=raw_data.get("id") or "unknown",
            page_id=page_id,
            platform=self.platform,
            text=raw_data.get("title") or raw_data.get("description"),
            reactions_count=raw_data.get("likes", 0),
            comments_count=raw_data.get("numberOfComments", 0),
            views_count=raw_data.get("viewCount", 0),
            created_time_iso=raw_data.get("date"),
            metadata=raw_data
        )

    def normalize_comment(self, raw_data: Dict[str, Any], post_id: str) -> NormalizedComment:
        return NormalizedComment(
            comment_id=raw_data.get("id") or "unknown",
            post_id=post_id,
            text=raw_data.get("text"),
            reactions_count=raw_data.get("likes", 0),
            created_time_iso=raw_data.get("publishedAt"),
            metadata=raw_data
        )

youtube_ingestion_service = YouTubeIngestionService()
