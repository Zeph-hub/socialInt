from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class NormalizedPage(BaseModel):
    page_id: str
    platform: str
    page_name: Optional[str] = None
    username: Optional[str] = None
    followers_count: int = 0
    profile_url: Optional[str] = None
    verified_status: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

class NormalizedPost(BaseModel):
    post_id: str
    page_id: str
    platform: str
    text: Optional[str] = None
    hashtags: List[str] = Field(default_factory=list)
    media_urls: List[str] = Field(default_factory=list)
    reactions_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    views_count: int = 0
    created_time_iso: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class NormalizedComment(BaseModel):
    comment_id: str
    post_id: str
    username: Optional[str] = None
    text: Optional[str] = None
    reactions_count: int = 0
    created_time_iso: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class StandardizedOutput(BaseModel):
    RowId: int
    UniqueId: str
    Platform: str
    PageId: Optional[str] = None
    PostId: Optional[str] = None
    PostType: str = "post"
    Text: Optional[str] = None
    CreatedTimeISO: Optional[str] = None
    EngagementScore: int = 0
    ReactionCount: int = 0
    CommentCount: int = 0
    ShareCount: int = 0
    # AI and Analytics Fields
    AiSentiment: str = "Pending"
    DetectedLanguage: str = "Unknown"
    AiTopic: str = "General"
    AiCategory: str = "Other"
    RiskLevel: str = "Low"
    # Legacy fields for internal compatibility
    ai_sentiment: str = "pending"
    ai_category: str = "pending"
    ai_language: str = "unknown"
    record_type: str = "post" 
    IngestionTimestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
