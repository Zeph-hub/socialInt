from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Social Media Data Pipeline"
    API_V1_STR: str = "/api/v1"
    
    # API Keys 
    APIFY_API_TOKEN: str = ""
    ANTHROPIC_API_KEY: str = ""
    
    # Actor IDs
    ACTOR_X_ID: str = "apidojo/tweet-scraper"
    ACTOR_INSTAGRAM_ID: str = "apify/instagram-scraper"
    ACTOR_TIKTOK_ID: str = "clockworks/tiktok-profile-scraper"
    ACTOR_YOUTUBE_ID: str = "streamers/youtube-scraper"
    ACTOR_FACEBOOK_ID: str = "apify/facebook-pages-scraper"
    ACTOR_LINKEDIN_ID: str = "curious_coder/linkedin-profile-scraper"
    
    # Storage configuration
    DATA_DIR: str = "./data"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
