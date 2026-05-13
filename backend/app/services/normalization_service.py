import logging
from typing import List, Dict, Any
from app.schemas.ingestion import StandardizedOutput
from app.ai.language import language_service
from app.ingestion.tiktok.service import tiktok_ingestion_service
from app.ingestion.instagram.service import instagram_ingestion_service
from app.ingestion.facebook.service import facebook_ingestion_service
from app.ingestion.linkedin.service import linkedin_ingestion_service
from app.ingestion.x.service import x_ingestion_service
from app.ingestion.youtube.service import youtube_ingestion_service

logger = logging.getLogger(__name__)

class NormalizationService:
    def __init__(self):
        self.services = {
            "tiktok": tiktok_ingestion_service,
            "instagram": instagram_ingestion_service,
            "facebook": facebook_ingestion_service,
            "linkedin": linkedin_ingestion_service,
            "x": x_ingestion_service,
            "youtube": youtube_ingestion_service
        }

    def get_service(self, platform: str):
        return self.services.get(platform.lower())

    def normalize_to_standard(self, platform: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        service = self.get_service(platform)
        if not service:
            logger.warning(f"No normalization service for platform: {platform}")
            return []

        standardized_records = []
        row_id = 1
        
        for item in raw_data:
            try:
                page = service.normalize_page(item)
                
                posts = item.get("posts", item.get("videos", [item]))
                if not isinstance(posts, list):
                    posts = [posts]
                    
                for post_data in posts:
                    if not isinstance(post_data, dict): continue
                    
                    post = service.normalize_post(post_data, page.page_id)
                    
                    record = StandardizedOutput(
                        RowId=row_id,
                        UniqueId=post.post_id,
                        Platform=platform.upper(),
                        PageId=page.page_id,
                        PostId=post.post_id,
                        Text=post.text,
                        CreatedTimeISO=post.created_time_iso,
                        EngagementScore=post.reactions_count + post.comments_count + post.shares_count,
                        ReactionCount=post.reactions_count,
                        CommentCount=post.comments_count,
                        ShareCount=post.shares_count,
                        record_type="post",
                        DetectedLanguage=language_service.detect_language(post.text),
                        ai_language=language_service.detect_language(post.text)
                    )
                    standardized_records.append(record.model_dump())
                    row_id += 1
                    
                    # Handle comments if present
                    comments_data = post_data.get("comments", post_data.get("latestComments", []))
                    if isinstance(comments_data, list):
                        for comment_raw in comments_data:
                            if not isinstance(comment_raw, dict): continue
                            comment = service.normalize_comment(comment_raw, post.post_id)
                            comment_record = StandardizedOutput(
                                RowId=row_id,
                                UniqueId=comment.comment_id,
                                Platform=platform.upper(),
                                PageId=page.page_id,
                                PostId=post.post_id,
                                Text=comment.text,
                                CreatedTimeISO=comment.created_time_iso,
                                EngagementScore=comment.reactions_count,
                                ReactionCount=comment.reactions_count,
                                record_type="comment",
                                DetectedLanguage=language_service.detect_language(comment.text),
                                ai_language=language_service.detect_language(comment.text)
                            )
                            standardized_records.append(comment_record.model_dump())
                            row_id += 1
                    
            except Exception as e:
                logger.error(f"Error normalizing item for {platform}: {str(e)}")
                continue
                
        return standardized_records

normalization_service = NormalizationService()
