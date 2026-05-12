import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import logging
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)

TEXT_FIELDS = ("text", "caption", "description", "title", "content", "message", "comment", "body")
TIME_FIELDS = ("createTimeISO", "createTime", "createdAt", "timestamp", "publishedAt", "date", "time")
ID_FIELDS = ("id", "cid", "awemeId", "videoId", "postId", "shortCode", "url", "webVideoUrl", "videoWebUrl")
AUTHOR_FIELDS = ("uniqueId", "username", "ownerUsername", "authorMeta.name", "author.username", "author")

class ProcessingService:
    def __init__(self):
        pass

    def _first_value(self, item: Dict[str, Any], fields: tuple[str, ...]) -> Any:
        for field in fields:
            value = self._nested_value(item, field)
            if value not in (None, "", [], {}):
                return value
        return None

    def _nested_value(self, item: Dict[str, Any], field: str) -> Any:
        value: Any = item
        for part in field.split("."):
            if not isinstance(value, dict) or part not in value:
                return None
            value = value[part]
        return value

    def _coerce_iso_time(self, value: Any) -> Optional[str]:
        if value in (None, ""):
            return None
        if isinstance(value, (int, float)):
            timestamp = value / 1000 if value > 10_000_000_000 else value
            return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            if text.isdigit():
                return self._coerce_iso_time(int(text))
            return text
        return str(value)

    def _safe_int(self, value: Any) -> int:
        try:
            return int(float(value or 0))
        except (TypeError, ValueError):
            return 0

    def _detect_record_type(self, item: Dict[str, Any]) -> str:
        keys = {key.lower() for key in item.keys()}
        if {"comment", "cid"} & keys or "replycommenttotal" in keys:
            return "comment" if "cid" in keys else "post"
        if {"comments", "latestcomments"} & keys:
            return "post"
        if {"posts", "videos"} & keys:
            return "page"
        return "post"

    def _detect_language_basic(self, text: str) -> str:
        clean = (text or "").strip()
        if not clean:
            return "unknown"
        lowered = f" {clean.lower()} "
        hints = {
            "english": (" the ", " and ", " is ", " for ", " with ", " from "),
            "spanish": (" el ", " la ", " de ", " que ", " para ", " con "),
            "french": (" le ", " la ", " des ", " les ", " pour ", " avec "),
            "swahili": (" na ", " kwa ", " ni ", " ya ", " katika ", " habari "),
        }
        scores = {language: sum(marker in lowered for marker in markers) for language, markers in hints.items()}
        best_language, best_score = max(scores.items(), key=lambda item: item[1])
        if best_score:
            return best_language
        return "unknown"

    def _normalize_item(
        self,
        item: Dict[str, Any],
        platform: str,
        row_id: int,
        page_hint: Optional[str] = None,
        parent_post_id: Optional[str] = None,
        record_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        unique_id = self._first_value(item, ID_FIELDS) or f"{platform}-{row_id}"
        text = self._first_value(item, TEXT_FIELDS) or ""
        created = self._coerce_iso_time(self._first_value(item, TIME_FIELDS))
        author = self._first_value(item, AUTHOR_FIELDS)
        likes = self._safe_int(self._first_value(item, ("diggCount", "likes", "likeCount", "likesCount", "reactionCount", "reactions")))
        comments = self._safe_int(self._first_value(item, ("replyCommentTotal", "commentCount", "commentsCount", "comments")))
        shares = self._safe_int(self._first_value(item, ("shareCount", "shares", "reposts", "retweetCount")))
        views = self._safe_int(self._first_value(item, ("playCount", "viewCount", "views", "videoViewCount")))
        url = self._first_value(item, ("url", "videoWebUrl", "webVideoUrl", "link", "postUrl"))

        return {
            "Rowid": row_id,
            "Uniqueid": str(unique_id),
            "platform": platform,
            "record_type": record_type or self._detect_record_type(item),
            "page_id": str(page_hint or author or ""),
            "post_id": str(parent_post_id or unique_id),
            "parent_post_id": str(parent_post_id or ""),
            "author": str(author or ""),
            "text": str(text or ""),
            "ai_language": self._detect_language_basic(str(text or "")),
            "ai_sentiment": "pending",
            "ai_category": "pending",
            "Ai-language": self._detect_language_basic(str(text or "")),
            "Ai-sentiment": "pending",
            "Ai-category": "pending",
            "createtimeiso": created,
            "url": str(url or ""),
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "views": views,
            "engagement": likes + comments + shares,
        }

    def normalize_social_records(self, platform: str, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Converts mixed Apify page/post/comment payloads into a clean analytics schema.
        """
        rows: List[Dict[str, Any]] = []
        row_id = 1

        for item in data:
            if not isinstance(item, dict):
                continue

            page_hint = self._first_value(item, ("uniqueId", "username", "name", "pageName", "title"))
            post_collections = []
            for key in ("posts", "videos", "items", "latestPosts"):
                value = item.get(key)
                if isinstance(value, list):
                    post_collections.extend([entry for entry in value if isinstance(entry, dict)])

            if post_collections:
                rows.append(self._normalize_item(item, platform, row_id, page_hint=page_hint, record_type="page"))
                row_id += 1
                source_posts = post_collections
            else:
                source_posts = [item]

            for post in source_posts:
                post_id = str(self._first_value(post, ID_FIELDS) or f"{platform}-post-{row_id}")
                rows.append(self._normalize_item(post, platform, row_id, page_hint=page_hint, parent_post_id=post_id, record_type="post"))
                row_id += 1

                comments = []
                for key in ("comments", "latestComments", "topComments", "replies"):
                    value = post.get(key)
                    if isinstance(value, list):
                        comments.extend([entry for entry in value if isinstance(entry, dict)])

                for comment in comments:
                    rows.append(
                        self._normalize_item(
                            comment,
                            platform,
                            row_id,
                            page_hint=page_hint,
                            parent_post_id=post_id,
                            record_type="comment",
                        )
                    )
                    row_id += 1

        logger.info("Normalized %s raw items into %s analytics rows", len(data), len(rows))
        return rows

    def flatten_data(self, data: List[Dict[str, Any]], preserve_nested: bool = True) -> List[Dict[str, Any]]:
        """
        Processes raw Apify data for better usability while preserving structure.
        
        Args:
            data: Raw data from Apify
            preserve_nested: If True, keeps nested structures as JSON strings instead of flattening
        
        Returns:
            Processed data with optional flattening
        """
        try:
            if not data:
                return []
            
            if preserve_nested:
                # Keep nested structures intact but ensure JSON serializable
                processed_data = []
                for item in data:
                    processed_item = {}
                    for key, value in item.items():
                        # Keep complex types as-is for JSON serialization
                        processed_item[key] = value
                    processed_data.append(processed_item)
                logger.info("Data processed while preserving nested structures")
                return processed_data
            else:
                # Original flattening logic for backwards compatibility
                df = pd.json_normalize(data)
                
                for col in df.columns:
                    if df[col].apply(lambda x: isinstance(x, list)).any():
                        df[col] = df[col].apply(
                            lambda x: ", ".join([str(i) for i in x]) if isinstance(x, list) else x
                        )
                
                df = df.replace({np.nan: None})
                flattened_data = df.to_dict(orient="records")
                logger.info("Data flattened into tabular format")
                return flattened_data
            
        except Exception as e:
            logger.error(f"Error processing data: {str(e)}")
            raise e

    def process_and_save_data(self, platform: str, raw_filepath: str) -> str:
        """
        Loads raw JSON data from filepath, flattens it, and saves it to the processed directory.
        """
        try:
            with open(raw_filepath, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                
            flattened_data = self.normalize_social_records(platform, raw_data)
            
            processed_filepath = storage_service.save_processed_data(platform, flattened_data)
            logger.info(f"Successfully processed and saved {platform} data to {processed_filepath}")
            return processed_filepath
        except Exception as e:
            logger.error(f"Error in process_and_save_data for {platform}: {str(e)}")
            raise e

processing_service = ProcessingService()
