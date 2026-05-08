import json
import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.services.storage_service import storage_service

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
    
    # Find the most recent enriched file for the platform
    files = list(storage_service.processed_dir.glob(f"{platform}_processed_*_enriched.json"))
    if not files:
        # Fallback to just processed if no enriched file exists
        files = list(storage_service.processed_dir.glob(f"{platform}_processed_*.json"))
        if not files:
            raise HTTPException(status_code=404, detail=f"No processed data found for platform: {platform}")
            
    # Sort files by modification time (most recent first)
    latest_file = sorted(files, key=os.path.getmtime, reverse=True)[0]
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Apply filters
        if language:
            data = [item for item in data if item.get("ai_language", "").lower() == language.lower()]
        if sentiment:
            data = [item for item in data if item.get("ai_sentiment", "").lower() == sentiment.lower()]
        if category:
            data = [item for item in data if item.get("ai_category", "").lower() == category.lower()]
            
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
    data_response = get_platform_data(platform=platform, limit=10000, offset=0)
    data = data_response["data"]
    
    sentiment_counts = {}
    category_counts = {}
    language_counts = {}
    
    for item in data:
        sentiment = item.get("ai_sentiment", "unknown")
        category = item.get("ai_category", "unknown")
        language = item.get("ai_language", "unknown")
        
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        category_counts[category] = category_counts.get(category, 0) + 1
        language_counts[language] = language_counts.get(language, 0) + 1
        
    return {
        "platform": platform,
        "total_records": len(data),
        "sentiment_distribution": sentiment_counts,
        "category_distribution": category_counts,
        "language_distribution": language_counts
    }
