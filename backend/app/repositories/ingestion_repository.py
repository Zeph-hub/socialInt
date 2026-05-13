import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)

class IngestionRepository:
    """
    Repository for managing persisted ingestion data.
    Currently uses file-based storage, but can be refactored to SQL/NoSQL.
    """
    
    def save_raw(self, platform: str, data: List[Dict[str, Any]]) -> str:
        """Save raw JSON data and return its path."""
        return storage_service.save_raw_data(platform, data)

    def save_processed(self, platform: str, data: List[Dict[str, Any]]) -> str:
        """Save normalized/processed data and return its path."""
        return storage_service.save_processed_data(platform, data)

    def get_latest_processed(self, platform: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieve the latest processed data for a platform."""
        platform = platform.lower()
        files = list(storage_service.processed_dir.glob(f"{platform}_processed_*.json"))
        if not files:
            return None
        
        latest_file = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading latest processed file {latest_file}: {e}")
            return None

ingestion_repository = IngestionRepository()
