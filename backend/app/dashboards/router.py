import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.analytics.service import analysis_service

router = APIRouter(prefix="/powerbi", tags=["powerbi"])

@router.get("/data/{platform}")
def get_platform_data(
    platform: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    language: Optional[str] = None,
    sentiment: Optional[str] = None,
    category: Optional[str] = None
):
    """
    Retrieves the latest enriched data for a given platform, suitable for Power BI consumption.
    Supports filtering by language, sentiment, and category, as well as pagination.
    """
    platform = platform.lower()
    
    latest_file = analysis_service.latest_processed_file(platform)
    if not latest_file:
        raise HTTPException(status_code=404, detail=f"No processed data found for platform: {platform}")
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Apply filters
        if language:
            data = [item for item in data if item.get("ai_language", item.get("Ai-language", "")).lower() == language.lower()]
        if sentiment:
            data = [item for item in data if item.get("ai_sentiment", item.get("Ai-sentiment", "")).lower() == sentiment.lower()]
        if category:
            data = [item for item in data if item.get("ai_category", item.get("Ai-category", "")).lower() == category.lower()]
            
        # Apply pagination
        total_records = len(data)
        paginated_data = data[offset:offset + limit]
        
        return {
            "platform": platform,
            "total_records": total_records,
            "limit": limit,
            "offset": offset,
            "source_file": latest_file.name,
            "data": paginated_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading data: {str(e)}")

@router.get("/summary/{platform}")
def get_platform_summary(platform: str):
    """
    Returns a brief aggregate summary for a specific platform's latest data.
    """
    analysis = analysis_service.analyze_platform(platform)
    return {
        "platform": platform,
        "total_records": analysis["total_records"],
        "total_posts": analysis["total_posts"],
        "total_comments": analysis["total_comments"],
        "total_engagement": analysis["total_engagement"],
        "average_engagement": analysis["average_engagement"],
        "predicted_trend": analysis["predicted_trend"],
        "sentiment_distribution": analysis["sentiment_distribution"],
        "category_distribution": analysis["category_distribution"],
        "language_distribution": analysis["language_distribution"],
        "record_type_distribution": analysis["record_type_distribution"],
    }
