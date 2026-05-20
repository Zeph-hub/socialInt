import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
import pandas as pd
from app.storage.manager import storage

router = APIRouter(prefix="/analytics", tags=["analytics"])

def _load_all_processed_data(platform: Optional[str] = None) -> pd.DataFrame:
    """Loads all processed data into a Pandas DataFrame."""
    all_data = []
    
    if not os.path.exists(storage.processed_dir):
        return pd.DataFrame()
        
    platforms_to_check = [platform] if platform else os.listdir(storage.processed_dir)
    
    for plt in platforms_to_check:
        plt_path = os.path.join(storage.processed_dir, plt)
        if not os.path.exists(plt_path) or not os.path.isdir(plt_path):
            continue
            
        for date_str in os.listdir(plt_path):
            date_path = os.path.join(plt_path, date_str)
            if not os.path.isdir(date_path):
                continue
                
            for filename in os.listdir(date_path):
                if filename.endswith(".json"):
                    filepath = os.path.join(date_path, filename)
                    data = storage.load_processed_data(filepath)
                    all_data.extend(data)
                    
    return pd.DataFrame(all_data)

@router.get("/posts")
def get_analytics_posts(
    platform: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("timestamp", regex="^(timestamp|likes|comments|shares)$"),
    order: str = Query("desc", regex="^(asc|desc)$")
):
    """Get processed posts ready for analytics platforms."""
    df = _load_all_processed_data(platform)
    if df.empty:
        return []
        
    # Sort
    ascending = order == "asc"
    if sort_by in df.columns:
        df = df.sort_values(by=sort_by, ascending=ascending)
        
    # Paginate
    df_page = df.iloc[offset:offset+limit]
    
    # Handle NaN values before returning
    df_page = df_page.fillna("")
    return df_page.to_dict(orient="records")

@router.get("/sentiment")
def get_analytics_sentiment(platform: Optional[str] = None):
    """Aggregate sentiment analysis for PowerBI."""
    df = _load_all_processed_data(platform)
    if df.empty or "sentiment" not in df.columns:
        return []
        
    # Filter out missing sentiments
    df_filtered = df[df["sentiment"].notna() & (df["sentiment"] != "")]
    
    # Group by platform and sentiment
    summary = df_filtered.groupby(["platform", "sentiment"]).size().reset_index(name="count")
    return summary.to_dict(orient="records")

@router.get("/languages")
def get_analytics_languages(platform: Optional[str] = None):
    """Aggregate language distributions for PowerBI."""
    df = _load_all_processed_data(platform)
    if df.empty or "language" not in df.columns:
        return []
        
    df_filtered = df[df["language"].notna() & (df["language"] != "")]
    summary = df_filtered.groupby(["platform", "language"]).size().reset_index(name="count")
    return summary.to_dict(orient="records")

@router.get("/trends")
def get_analytics_trends(platform: Optional[str] = None):
    """Aggregate posts volume over time."""
    df = _load_all_processed_data(platform)
    if df.empty or "timestamp" not in df.columns:
        return []
        
    # Attempt to convert timestamp to datetime, ignoring errors
    df["date"] = pd.to_datetime(df["timestamp"], errors="coerce").dt.date
    df_filtered = df[df["date"].notna()]
    
    summary = df_filtered.groupby(["platform", "date"]).size().reset_index(name="post_count")
    # Convert date to string for JSON serialization
    summary["date"] = summary["date"].astype(str)
    
    return summary.to_dict(orient="records")
