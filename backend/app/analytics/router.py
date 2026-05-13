from fastapi import APIRouter, HTTPException

from app.analytics.service import analysis_service

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/{platform}")
def get_platform_analysis(platform: str):
    try:
        return analysis_service.analyze_platform(platform)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing data: {str(e)}")
