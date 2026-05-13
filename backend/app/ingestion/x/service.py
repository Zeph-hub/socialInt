import logging
from typing import List, Dict, Any
from apify_client import ApifyClient
from app.config.settings import settings
from app.ingestion.base import BaseIngestionService
from app.schemas.ingestion import NormalizedPage, NormalizedPost, NormalizedComment

logger = logging.getLogger(__name__)

class XIngestionService(BaseIngestionService):
    platform = "x"

    def __init__(self):
        super().__init__()
        self.client = ApifyClient(settings.APIFY_API_TOKEN) if settings.APIFY_API_TOKEN else None

    def fetch_data(self, targets: List[str], posts_per_page: int = 100, comments_per_post: int = 100, **kwargs) -> List[Dict[str, Any]]:
        if not self.client:
            raise ValueError("Apify API token is not configured")
            
        actor_id = settings.ACTOR_X_ID
        run_input = {
            "searchTerms": targets,
            "maxItems": posts_per_page,
            "maxReplies": comments_per_post,
        }
        
        logger.info(f"Running X actor {actor_id}")
        run = self.client.actor(actor_id).call(run_input=run_input)
        return list(self.client.dataset(run["defaultDatasetId"]).iterate_items())

    def normalize_page(self, raw_data: Dict[str, Any]) -> NormalizedPage:
        user = raw_data.get("user", {})
        return NormalizedPage(
            page_id=user.get("id") or "unknown",
            platform=self.platform,
            page_name=user.get("name"),
            username=user.get("screen_name"),
            followers_count=user.get("followers_count", 0),
            profile_url=f"https://x.com/{user.get('screen_name')}" if user.get('screen_name') else None,
            verified_status=user.get("verified", False),
            metadata=raw_data
        )

    def normalize_post(self, raw_data: Dict[str, Any], page_id: str) -> NormalizedPost:
        return NormalizedPost(
            post_id=raw_data.get("id_str") or "unknown",
            page_id=page_id,
            platform=self.platform,
            text=raw_data.get("full_text") or raw_data.get("text"),
            reactions_count=raw_data.get("favorite_count", 0),
            comments_count=raw_data.get("reply_count", 0),
            shares_count=raw_data.get("retweet_count", 0),
            created_time_iso=raw_data.get("created_at"),
            metadata=raw_data
        )

    def normalize_comment(self, raw_data: Dict[str, Any], post_id: str) -> NormalizedComment:
        return NormalizedComment(
            comment_id=raw_data.get("id_str") or "unknown",
            post_id=post_id,
            username=raw_data.get("user", {}).get("screen_name"),
            text=raw_data.get("full_text") or raw_data.get("text"),
            reactions_count=raw_data.get("favorite_count", 0),
            created_time_iso=raw_data.get("created_at"),
            metadata=raw_data
        )

x_ingestion_service = XIngestionService()
