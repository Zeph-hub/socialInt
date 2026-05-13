import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from app.config.settings import settings

class StorageService:
    def __init__(self):
        self.data_dir = Path(settings.DATA_DIR)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        
        # Ensure directories exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def save_raw_data(self, platform: str, data: List[Dict[str, Any]]) -> str:
        """
        Saves raw data from Apify to a JSON file exactly as received (no transformation).
        This ensures the saved data matches the Apify dashboard output.
        Returns the path to the saved file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{platform}_{timestamp}.json"
        filepath = self.raw_dir / filename
        
        # Save the data exactly as returned from Apify, no processing
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Log data summary for verification
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Saved {len(data)} raw items from {platform} to {filepath}")
        if data:
            logger.debug(f"Sample raw item keys: {list(data[0].keys())}")
            
        return str(filepath)
        
    def save_processed_data(self, platform: str, data: List[Dict[str, Any]]) -> str:
        """
        Saves processed data (flattened, classified) to a JSON file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{platform}_processed_{timestamp}.json"
        filepath = self.processed_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return str(filepath)

storage_service = StorageService()
