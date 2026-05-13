import logging
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.services.storage_service import storage_service
from app.schemas.ingestion import NormalizedPage, NormalizedPost, NormalizedComment

logger = logging.getLogger(__name__)

class BaseIngestionService(ABC):
    platform: str = ""

    def __init__(self):
        if not self.platform:
            raise ValueError("Ingestion service must define a platform name")

    @abstractmethod
    def fetch_data(self, targets: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Fetch raw data from external source (Apify)."""
        pass

    @abstractmethod
    def normalize_page(self, raw_data: Dict[str, Any]) -> NormalizedPage:
        pass

    @abstractmethod
    def normalize_post(self, raw_data: Dict[str, Any], page_id: str) -> NormalizedPost:
        pass

    @abstractmethod
    def normalize_comment(self, raw_data: Dict[str, Any], post_id: str) -> NormalizedComment:
        pass

    def save_raw_data(self, data: List[Dict[str, Any]]) -> str:
        """Persist raw JSON data."""
        return storage_service.save_raw_data(self.platform, data)

    def run_with_retry(self, func, *args, max_retries=3, delay=5, **kwargs):
        """Simple retry logic for external API calls."""
        last_exception = None
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed for {self.platform}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))
        
        logger.error(f"All {max_retries} attempts failed for {self.platform}")
        raise last_exception

    def process_ingestion(self, targets: List[str], **kwargs) -> Dict[str, Any]:
        """Main ingestion flow: Fetch -> Save Raw -> Normalize -> Save Processed."""
        logger.info(f"Starting ingestion for {self.platform} with targets: {targets}")
        
        raw_data = self.run_with_retry(self.fetch_data, targets, **kwargs)
        raw_filepath = self.save_raw_data(raw_data)
        
        # In a real implementation, we would normalize and save here.
        # For now, we return the raw filepath to maintain compatibility with the current flow.
        return {
            "platform": self.platform,
            "raw_filepath": raw_filepath,
            "count": len(raw_data)
        }
