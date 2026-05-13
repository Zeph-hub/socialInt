import logging
from typing import List, Dict, Any
from apify_client import ApifyClient
from app.config.settings import settings
from app.ingestion.base import BaseIngestionService
from app.schemas.ingestion import NormalizedPage, NormalizedPost, NormalizedComment

logger = logging.getLogger(__name__)

class TikTokIngestionService(BaseIngestionService):
    platform = "tiktok"

    def __init__(self):
        super().__init__()
        self.client = ApifyClient(settings.APIFY_API_TOKEN) if settings.APIFY_API_TOKEN else None

    def fetch_data(self, targets: List[str], posts_per_page: int = 100, comments_per_post: int = 100, **kwargs) -> List[Dict[str, Any]]:
        if not self.client:
            raise ValueError("Apify API token is not configured")
            
        actor_id = settings.ACTOR_TIKTOK_ID
        run_input = self._build_input(targets, posts_per_page, comments_per_post)
        
        logger.info(f"Running TikTok actor {actor_id}")
        run = self.client.actor(actor_id).call(run_input=run_input)
        return list(self.client.dataset(run["defaultDatasetId"]).iterate_items())

    def _build_input(self, targets: List[str], posts_per_page: int, comments_per_post: int) -> Dict[str, Any]:
        actor_id = settings.ACTOR_TIKTOK_ID.lower()
        if "tiktok-comments-scraper" in actor_id:
            return {
                "postURLs": targets,
                "commentsPerPost": comments_per_post,
                "maxRepliesPerComment": 0,
                "resultsPerPage": posts_per_page,
            }
        return {
            "profiles": [target.lstrip("@") for target in targets],
            "resultsPerPage": posts_per_page,
            "commentsPerPost": comments_per_post,
        }

    def normalize_page(self, raw_data: Dict[str, Any]) -> NormalizedPage:
        return NormalizedPage(
            page_id=raw_data.get("uniqueId") or raw_data.get("id") or "unknown",
            platform=self.platform,
            page_name=raw_data.get("nickname"),
            username=raw_data.get("uniqueId"),
            followers_count=raw_data.get("followerCount", 0),
            profile_url=f"https://www.tiktok.com/@{raw_data.get('uniqueId')}" if raw_data.get("uniqueId") else None,
            verified_status=raw_data.get("verified", False),
            metadata=raw_data
        )

    def normalize_post(self, raw_data: Dict[str, Any], page_id: str) -> NormalizedPost:
        return NormalizedPost(
            post_id=raw_data.get("id") or "unknown",
            page_id=page_id,
            platform=self.platform,
            text=raw_data.get("desc"),
            hashtags=[tag.get("title") for tag in raw_data.get("textExtra", []) if tag.get("title")],
            media_urls=[raw_data.get("video", {}).get("downloadAddr")] if raw_data.get("video") else [],
            reactions_count=raw_data.get("diggCount", 0),
            comments_count=raw_data.get("commentCount", 0),
            shares_count=raw_data.get("shareCount", 0),
            views_count=raw_data.get("playCount", 0),
            created_time_iso=raw_data.get("createTimeISO"),
            metadata=raw_data
        )

    def normalize_comment(self, raw_data: Dict[str, Any], post_id: str) -> NormalizedComment:
        return NormalizedComment(
            comment_id=raw_data.get("cid") or "unknown",
            post_id=post_id,
            username=raw_data.get("user", {}).get("uniqueId"),
            text=raw_data.get("text"),
            reactions_count=raw_data.get("diggCount", 0),
            created_time_iso=raw_data.get("createTimeISO"),
            metadata=raw_data
        )

tiktok_ingestion_service = TikTokIngestionService()
