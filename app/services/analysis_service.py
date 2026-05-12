import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.storage_service import storage_service


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

    def _counter(self, rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
        return dict(Counter(str(row.get(key) or "unknown").lower() for row in rows))

    def _sentiment_score(self, sentiment: str) -> int:
        normalized = (sentiment or "").lower()
        if normalized == "positive":
            return 1
        if normalized == "negative":
            return -1
        return 0

    def analyze_platform(self, platform: str) -> Dict[str, Any]:
        latest_file, rows = self.load_latest_records(platform)
        posts = [row for row in rows if row.get("record_type") == "post"]
        comments = [row for row in rows if row.get("record_type") == "comment"]

        sentiment_distribution = self._counter(rows, "ai_sentiment")
        language_distribution = self._counter(rows, "ai_language")
        category_distribution = self._counter(rows, "ai_category")
        record_type_distribution = self._counter(rows, "record_type")

        post_comments: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for comment in comments:
            post_comments[str(comment.get("parent_post_id") or "")].append(comment)

        post_performance = []
        for post in posts:
            related_comments = post_comments.get(str(post.get("post_id") or post.get("Uniqueid") or ""), [])
            comment_sentiment_score = sum(self._sentiment_score(comment.get("ai_sentiment", "")) for comment in related_comments)
            total_comments = len(related_comments)
            post_performance.append(
                {
                    "post_id": post.get("post_id"),
                    "page_id": post.get("page_id"),
                    "text": post.get("text"),
                    "url": post.get("url"),
                    "createtimeiso": post.get("createtimeiso"),
                    "engagement": post.get("engagement", 0),
                    "likes": post.get("likes", 0),
                    "comments": post.get("comments", total_comments),
                    "shares": post.get("shares", 0),
                    "comment_rows": total_comments,
                    "comment_sentiment_score": comment_sentiment_score,
                    "avg_comment_sentiment": round(comment_sentiment_score / total_comments, 3) if total_comments else 0,
                    "ai_sentiment": post.get("ai_sentiment"),
                    "ai_category": post.get("ai_category"),
                }
            )

        post_performance.sort(key=lambda row: row.get("engagement") or 0, reverse=True)
        total_engagement = sum(int(row.get("engagement") or 0) for row in posts)
        avg_engagement = round(total_engagement / len(posts), 2) if posts else 0
        positive = sentiment_distribution.get("positive", 0)
        negative = sentiment_distribution.get("negative", 0)
        sentiment_balance = round((positive - negative) / len(rows), 3) if rows else 0

        trend = "stable"
        if sentiment_balance > 0.2:
            trend = "improving"
        elif sentiment_balance < -0.2:
            trend = "at risk"

        top_categories = sorted(category_distribution.items(), key=lambda item: item[1], reverse=True)[:3]
        insights = [
            f"Audience sentiment is {trend} with a net score of {sentiment_balance}.",
            f"Average post engagement is {avg_engagement}.",
        ]
        if top_categories:
            insights.append(f"Most discussed topic is {top_categories[0][0]} across {top_categories[0][1]} records.")
        if post_performance:
            best = post_performance[0]
            insights.append(f"Top post has {best.get('engagement', 0)} engagements and {best.get('avg_comment_sentiment', 0)} average comment sentiment.")

        return {
            "platform": platform.lower(),
            "source_file": latest_file.name if latest_file else None,
            "total_records": len(rows),
            "total_posts": len(posts),
            "total_comments": len(comments),
            "total_engagement": total_engagement,
            "average_engagement": avg_engagement,
            "sentiment_balance": sentiment_balance,
            "predicted_trend": trend,
            "sentiment_distribution": sentiment_distribution,
            "language_distribution": language_distribution,
            "category_distribution": category_distribution,
            "record_type_distribution": record_type_distribution,
            "top_posts": post_performance[:10],
            "insights": insights,
        }


analysis_service = AnalysisService()
