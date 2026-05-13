import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)

class PredictiveService:
    def forecast_engagement(self, history: List[Dict[str, Any]], periods: int = 7) -> List[float]:
        """
        Forecasts future engagement using Holt-Winters Exponential Smoothing.
        """
        if len(history) < 14: # Need at least 2 weeks of data for meaningful forecast
            return []
            
        try:
            df = pd.DataFrame(history)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').set_index('date')
            
            # Resample to daily engagement
            daily = df['engagement'].resample('D').sum().fillna(0)
            
            model = ExponentialSmoothing(daily, seasonal='add', seasonal_periods=7).fit()
            forecast = model.forecast(periods)
            return forecast.tolist()
        except Exception as e:
            logger.error(f"Forecasting failed: {e}")
            return []

    def detect_anomalies(self, data: List[Dict[str, Any]]) -> List[int]:
        """
        Identifies engagement anomalies using Isolation Forest.
        Returns a list of indices where anomalies were detected.
        """
        if not data:
            return []
            
        try:
            df = pd.DataFrame(data)
            X = df[['engagement', 'reactions', 'comments']].fillna(0)
            
            clf = IsolationForest(contamination=0.05, random_state=42)
            preds = clf.fit_predict(X)
            
            # -1 indicates anomaly
            return [i for i, val in enumerate(preds) if val == -1]
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return []

    def predict_sentiment_trend(self, history: List[Dict[str, Any]]) -> str:
        """Predicts if sentiment is likely to improve or decline."""
        if len(history) < 5:
            return "Stable"
            
        try:
            df = pd.DataFrame(history)
            df['sentiment_score'] = df['sentiment'].map({"Positive": 1, "Neutral": 0, "Negative": -1, "Mixed": 0})
            
            # Simple linear trend on the last 10 points
            y = df['sentiment_score'].tail(10).values
            x = np.arange(len(y))
            slope = np.polyfit(x, y, 1)[0]
            
            if slope > 0.1: return "Improving"
            if slope < -0.1: return "Declining"
            return "Stable"
        except Exception as e:
            logger.error(f"Sentiment prediction failed: {e}")
            return "Stable"

predictive_service = PredictiveService()
