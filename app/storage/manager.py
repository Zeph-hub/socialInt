import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.utils.logger import log

class StorageManager:
    def __init__(self, base_dir: str = "storage"):
        self.base_dir = os.path.abspath(base_dir)
        self.raw_dir = os.path.join(self.base_dir, "raw")
        self.processed_dir = os.path.join(self.base_dir, "processed")
        self.pipelines_dir = os.path.join(self.base_dir, "pipelines")
        
        # Ensure directories exist
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.pipelines_dir, exist_ok=True)

    def _get_date_str(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def save_raw_payload(self, platform: str, payload: List[Dict[str, Any]], pipeline_id: str) -> str:
        """Saves raw data payload as JSON."""
        date_str = self._get_date_str()
        platform_dir = os.path.join(self.raw_dir, platform, date_str)
        os.makedirs(platform_dir, exist_ok=True)
        
        filepath = os.path.join(platform_dir, f"{pipeline_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            
        log.info("Saved raw payload", platform=platform, pipeline_id=pipeline_id, filepath=filepath)
        return filepath

    def load_raw_payload(self, filepath: str) -> List[Dict[str, Any]]:
        """Loads a raw data payload from JSON."""
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
            
    def save_processed_data(self, platform: str, data: List[Dict[str, Any]], pipeline_id: str) -> str:
        """Saves processed/transformed data as JSON."""
        date_str = self._get_date_str()
        platform_dir = os.path.join(self.processed_dir, platform, date_str)
        os.makedirs(platform_dir, exist_ok=True)
        
        filepath = os.path.join(platform_dir, f"{pipeline_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        log.info("Saved processed data", platform=platform, pipeline_id=pipeline_id, filepath=filepath)
        return filepath

    def load_processed_data(self, filepath: str) -> List[Dict[str, Any]]:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_pipeline_metadata(self, pipeline_id: str, metadata: Dict[str, Any]) -> str:
        """Saves pipeline execution metadata."""
        filepath = os.path.join(self.pipelines_dir, f"{pipeline_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            # handle datetime serialization
            def default_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Type {type(obj)} not serializable")
            
            json.dump(metadata, f, ensure_ascii=False, indent=2, default=default_serializer)
        return filepath

    def load_pipeline_metadata(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        filepath = os.path.join(self.pipelines_dir, f"{pipeline_id}.json")
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_pipelines(self) -> List[Dict[str, Any]]:
        pipelines = []
        if os.path.exists(self.pipelines_dir):
            for filename in os.listdir(self.pipelines_dir):
                if filename.endswith(".json"):
                    with open(os.path.join(self.pipelines_dir, filename), "r", encoding="utf-8") as f:
                        try:
                            pipelines.append(json.load(f))
                        except Exception as e:
                            log.error("Failed to load pipeline metadata", file=filename, error=str(e))
        return pipelines

storage = StorageManager()
