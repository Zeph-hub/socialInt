import pandas as pd
from typing import Any, Dict, List
from app.utils.logger import log

class DataTransformer:
    def process(self, platform: str, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not raw_data:
            return []
            
        log.info("Starting data transformation", platform=platform, records=len(raw_data))
        df = pd.json_normalize(raw_data)
        
        # Standard schema
        # {
        #     "platform", "content", "author", "likes", "comments",
        #     "shares", "timestamp", "language", "sentiment"
        # }
        
        normalized_df = pd.DataFrame()
        normalized_df["platform"] = platform
        
        # Mapping logic per platform
        if platform == "tiktok":
            normalized_df["content"] = df.get("text", df.get("desc", ""))
            normalized_df["author"] = df.get("authorMeta.name", df.get("author.nickname", ""))
            normalized_df["likes"] = df.get("diggCount", df.get("stats.diggCount", 0))
            normalized_df["comments"] = df.get("commentCount", df.get("stats.commentCount", 0))
            normalized_df["shares"] = df.get("shareCount", df.get("stats.shareCount", 0))
            normalized_df["timestamp"] = df.get("createTime", df.get("createTimeISO", ""))
        elif platform == "instagram":
            normalized_df["content"] = df.get("caption", "")
            normalized_df["author"] = df.get("ownerUsername", "")
            normalized_df["likes"] = df.get("likesCount", 0)
            normalized_df["comments"] = df.get("commentsCount", 0)
            normalized_df["shares"] = 0 # Instagram often hides shares
            normalized_df["timestamp"] = df.get("timestamp", "")
        elif platform == "x":
            normalized_df["content"] = df.get("full_text", df.get("text", ""))
            normalized_df["author"] = df.get("user.screen_name", "")
            normalized_df["likes"] = df.get("favorite_count", df.get("likes", 0))
            normalized_df["comments"] = df.get("reply_count", df.get("replies", 0))
            normalized_df["shares"] = df.get("retweet_count", df.get("retweets", 0))
            normalized_df["timestamp"] = df.get("created_at", "")
        elif platform == "facebook":
            normalized_df["content"] = df.get("text", "")
            normalized_df["author"] = df.get("user.name", "")
            normalized_df["likes"] = df.get("likes", 0)
            normalized_df["comments"] = df.get("comments", 0)
            normalized_df["shares"] = df.get("shares", 0)
            normalized_df["timestamp"] = df.get("time", "")
        elif platform == "youtube":
            normalized_df["content"] = df.get("title", "") + " " + df.get("description", "")
            normalized_df["author"] = df.get("channelName", "")
            normalized_df["likes"] = df.get("likes", 0)
            normalized_df["comments"] = df.get("commentsCount", 0)
            normalized_df["shares"] = 0
            normalized_df["timestamp"] = df.get("date", "")
        elif platform == "linkedin":
            normalized_df["content"] = df.get("text", "")
            normalized_df["author"] = df.get("author.firstName", "") + " " + df.get("author.lastName", "")
            normalized_df["likes"] = df.get("numLikes", 0)
            normalized_df["comments"] = df.get("numComments", 0)
            normalized_df["shares"] = df.get("numShares", 0)
            normalized_df["timestamp"] = df.get("postDate", "")
        else:
            # Fallback
            normalized_df["content"] = df.get("text", df.get("caption", ""))
            normalized_df["author"] = ""
            normalized_df["likes"] = 0
            normalized_df["comments"] = 0
            normalized_df["shares"] = 0
            normalized_df["timestamp"] = ""

        # Default fields for AI enrichment
        normalized_df["language"] = None
        normalized_df["sentiment"] = None

        # Clean up missing data safely
        normalized_df.fillna({
            "content": "",
            "author": "Unknown",
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "timestamp": pd.Timestamp.now().isoformat()
        }, inplace=True)
        
        # Remove duplicates based on content if necessary
        normalized_df.drop_duplicates(subset=["content"], inplace=True)
        
        # Convert to dict
        processed_data = normalized_df.to_dict(orient="records")
        log.info("Data transformation completed", records_after=len(processed_data))
        return processed_data

data_transformer = DataTransformer()
