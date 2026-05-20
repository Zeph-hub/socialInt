import asyncio
from typing import Any, Dict, List
from apify_client import ApifyClient
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.utils.logger import log

class ApifyIngestionClient:
    def __init__(self):
        self.client = ApifyClient(settings.APIFY_API_TOKEN) if settings.APIFY_API_TOKEN else None

    def _ensure_client(self):
        if not self.client:
            raise ValueError("Apify API token is not configured. Please set APIFY_API_TOKEN in .env")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def run_actor_async(self, actor_id: str, run_input: Dict[str, Any]) -> List[Dict[str, Any]]:
        self._ensure_client()
        log.info("Starting Apify actor", actor_id=actor_id, run_input=run_input)
        
        # ApifyClient is synchronous, so we run it in a thread pool to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        
        def _run():
            run = self.client.actor(actor_id).call(run_input=run_input)
            dataset_id = run["defaultDatasetId"]
            return list(self.client.dataset(dataset_id).iterate_items())
            
        results = await loop.run_in_executor(None, _run)
        
        log.info("Actor finished", actor_id=actor_id, result_count=len(results))
        if not results:
            log.warning("Actor finished but returned 0 dataset items", actor_id=actor_id)
            
        return results

    def build_tiktok_input(self, targets: List[str], posts_per_page: int, comments_per_post: int) -> Dict[str, Any]:
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

    async def fetch_data(self, platform: str, targets: List[str], posts_per_page: int = 100, comments_per_post: int = 100) -> List[Dict[str, Any]]:
        platform = platform.lower()
        if platform == "tiktok":
            run_input = self.build_tiktok_input(targets, posts_per_page, comments_per_post)
            return await self.run_actor_async(settings.ACTOR_TIKTOK_ID, run_input)
        elif platform == "instagram":
            run_input = {
                "directUrls": [f"https://www.instagram.com/{u}/" for u in targets],
                "resultsType": "details",
                "resultsLimit": posts_per_page,
                "commentsLimit": comments_per_post,
            }
            return await self.run_actor_async(settings.ACTOR_INSTAGRAM_ID, run_input)
        elif platform == "x":
            run_input = {
                "searchTerms": targets,
                "maxItems": posts_per_page,
                "maxReplies": comments_per_post,
            }
            return await self.run_actor_async(settings.ACTOR_X_ID, run_input)
        elif platform == "facebook":
            run_input = {
                "startUrls": [{"url": p} for p in targets],
                "maxPosts": posts_per_page,
                "maxComments": comments_per_post,
            }
            return await self.run_actor_async(settings.ACTOR_FACEBOOK_ID, run_input)
        elif platform == "youtube":
            run_input = {
                "startUrls": [{"url": c} for c in targets],
                "maxResults": posts_per_page,
                "maxComments": comments_per_post,
            }
            return await self.run_actor_async(settings.ACTOR_YOUTUBE_ID, run_input)
        elif platform == "linkedin":
            run_input = {
                "urls": targets,
                "maxPosts": posts_per_page,
                "maxComments": comments_per_post,
            }
            return await self.run_actor_async(settings.ACTOR_LINKEDIN_ID, run_input)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

apify_client = ApifyIngestionClient()
