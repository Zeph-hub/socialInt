from typing import Dict, Optional
from app.ingestion.base import BaseIngestionService
from app.ingestion.tiktok.service import tiktok_ingestion_service
from app.ingestion.instagram.service import instagram_ingestion_service
from app.ingestion.facebook.service import facebook_ingestion_service
from app.ingestion.linkedin.service import linkedin_ingestion_service
from app.ingestion.x.service import x_ingestion_service
from app.ingestion.youtube.service import youtube_ingestion_service

class IngestionFactory:
    def __init__(self):
        self._services: Dict[str, BaseIngestionService] = {
            "tiktok": tiktok_ingestion_service,
            "instagram": instagram_ingestion_service,
            "facebook": facebook_ingestion_service,
            "linkedin": linkedin_ingestion_service,
            "x": x_ingestion_service,
            "youtube": youtube_ingestion_service
        }

    def get_service(self, platform: str) -> Optional[BaseIngestionService]:
        return self._services.get(platform.lower())

ingestion_factory = IngestionFactory()
