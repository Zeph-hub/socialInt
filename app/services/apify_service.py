import logging
from typing import Any, Dict, List
from apify_client import ApifyClient
from app.core.config import settings
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)

class ApifyService:
    def __init__(self):
        self.client = ApifyClient(settings.APIFY_API_TOKEN) if settings.APIFY_API_TOKEN else None

    def _ensure_client(self):
        if not self.client:
            raise ValueError("Apify API token is not configured. Please set APIFY_API_TOKEN in .env")

    def run_actor(self, actor_id: str, run_input: Dict[str, Any]) -> List[Dict[str, Any]]:
        self._ensure_client()
        logger.info(f"Starting Apify actor {actor_id}")
        logger.info(f"Run input: {run_input}")
        
        # Run the actor and wait for it to finish
        run = self.client.actor(actor_id).call(run_input=run_input)
        
        dataset_id = run["defaultDatasetId"]
        dataset_url = f"https://console.apify.com/storage/datasets/{dataset_id}"
        logger.info(f"Actor {actor_id} finished. Fetching results from dataset {dataset_id}")
        
        # iterate_items follows Apify's Python examples and avoids page-size surprises.
        results = list(self.client.dataset(dataset_id).iterate_items())
        
        logger.info(f"Retrieved {len(results)} items from dataset")
        if results:
            logger.debug(f"Sample item: {results[0]}")
        else:
            raise ValueError(
                f"Apify actor {actor_id} finished but returned 0 dataset items. "
                f"Check the run dataset here: {dataset_url}. "
                f"The most common cause is an input schema mismatch for this actor."
            )
        
        return results

    def _build_tiktok_input(self, targets: List[str]) -> Dict[str, Any]:
        actor_id = settings.ACTOR_TIKTOK_ID.lower()

        if "tiktok-comments-scraper" in actor_id:
            invalid_targets = [target for target in targets if not target.startswith(("http://", "https://"))]
            if invalid_targets:
                raise ValueError(
                    "ACTOR_TIKTOK_ID is configured as a TikTok comments scraper, "
                    "so targets must be TikTok video URLs, not usernames. "
                    f"Invalid targets: {invalid_targets}"
                )

            return {
                "postURLs": targets,
                "commentsPerPost": 100,
                "maxRepliesPerComment": 0,
                "resultsPerPage": 100,
            }

        return {
            "profiles": [target.lstrip("@") for target in targets],
            "resultsPerPage": 100,
        }

    def fetch_tiktok_data(self, targets: List[str]) -> str:
        run_input = self._build_tiktok_input(targets)
        data = self.run_actor(settings.ACTOR_TIKTOK_ID, run_input)
        return storage_service.save_raw_data("tiktok", data)

    def fetch_instagram_data(self, usernames: List[str]) -> str:
        run_input = {
            "directUrls": [f"https://www.instagram.com/{u}/" for u in usernames],
            "resultsType": "details",
        }
        data = self.run_actor(settings.ACTOR_INSTAGRAM_ID, run_input)
        return storage_service.save_raw_data("instagram", data)

    def fetch_x_data(self, search_terms: List[str]) -> str:
        run_input = {
            "searchTerms": search_terms,
            "maxItems": 100,
        }
        data = self.run_actor(settings.ACTOR_X_ID, run_input)
        return storage_service.save_raw_data("x", data)

    def fetch_facebook_data(self, pages: List[str]) -> str:
        run_input = {
            "startUrls": [{"url": p} for p in pages],
            "maxPosts": 100,
        }
        data = self.run_actor(settings.ACTOR_FACEBOOK_ID, run_input)
        return storage_service.save_raw_data("facebook", data)

    def fetch_youtube_data(self, channels: List[str]) -> str:
        run_input = {
            "startUrls": [{"url": c} for c in channels],
            "maxResults": 100,
        }
        data = self.run_actor(settings.ACTOR_YOUTUBE_ID, run_input)
        return storage_service.save_raw_data("youtube", data)

    def fetch_linkedin_data(self, urls: List[str]) -> str:
        run_input = {
            "urls": urls,
        }
        data = self.run_actor(settings.ACTOR_LINKEDIN_ID, run_input)
        return storage_service.save_raw_data("linkedin", data)

apify_service = ApifyService()
