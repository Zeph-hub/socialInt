import json
import os
import logging
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.services.storage_service import storage_service
from app.analytics.predictive import predictive_service

logger = logging.getLogger(__name__)

class AnalysisService:
    def latest_processed_file(self, platform: str) -> Optional[Path]:
        platform = platform.lower()
        enriched = list(storage_service.processed_dir.glob(f"{platform}_processed_*_enriched.json"))
        files = enriched or list(storage_service.processed_dir.glob(f"{platform}_processed_*.json"))
        if not files:
            return None
        return sorted(files, key=os.path.getmtime, reverse=True)[0]

    def load_latest_records(self, platform: str) -> tuple[Optional[Path], List[Dict[str, Any]]]:
        latest_file = self.latest_processed_file(platform)
        if latest_file is None:
            return None, []
        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return latest_file, data if isinstance(data, list) else [data]

    def analyze_platform(self, platform: str) -> Dict[str, Any]:
        latest_file, rows = self.load_latest_records(platform)
        if not rows:
            return {"error": "No data found"}

        # Basic filtering
        posts = [row for row in rows if row.get("record_type") == "post" or row.get("PostType") == "post"]
        
        # Viral Detection: Posts with engagement > 3x average
        avg_engagement = sum(row.get("engagement", 0) for row in posts) / len(posts) if posts else 0
        viral_posts = [row for row in posts if row.get("engagement", 0) > (avg_engagement * 3)]
        
        # Influencer Analysis: Group by page/author and sum engagement
        author_engagement = defaultdict(int)
        for row in posts:
            author = row.get("author") or row.get("PageId") or "unknown"
            author_engagement[author] += row.get("engagement", 0)
        
        top_influencers = sorted(author_engagement.items(), key=lambda x: x[1], reverse=True)[:5]

        # Time Series Aggregation
        time_series = []
        for row in posts:
            time_series.append({
                "date": row.get("createtimeiso") or row.get("CreatedTimeISO"),
                "engagement": row.get("engagement", 0),
                "sentiment": row.get("AiSentiment") or row.get("ai_sentiment", "Neutral")
            })
        
        # Predictive Analysis
        forecast = predictive_service.forecast_engagement(time_series)
        sentiment_trend = predictive_service.predict_sentiment_trend(time_series)

        return {
            "platform": platform,
            "total_records": len(rows),
            "viral_count": len(viral_posts),
            "top_influencers": [{"id": k, "impact": v} for k, v in top_influencers],
            "sentiment_trend": sentiment_trend,
            "forecast": forecast,
            "latest_file": str(latest_file.name) if latest_file else None,
            "sentiment_distribution": self._counter(rows, "AiSentiment", "ai_sentiment"),
            "category_distribution": self._counter(rows, "AiCategory", "ai_category"),
        }

    def _counter(self, rows: List[Dict[str, Any]], primary_key: str, fallback_key: str) -> Dict[str, int]:
        return dict(Counter(str(row.get(primary_key) or row.get(fallback_key) or "unknown") for row in rows))

analysis_service = AnalysisService()
