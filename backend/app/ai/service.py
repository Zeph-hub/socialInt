import json
import logging
from typing import List, Dict, Any, Optional
import anthropic
from app.config.settings import settings
from app.services.storage_service import storage_service
from app.ai.language import language_service

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        api_key = settings.ANTHROPIC_API_KEY.strip()
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None

    def _ensure_client(self):
        if not self.client:
            raise ValueError("Anthropic API key is not configured. Please set ANTHROPIC_API_KEY in .env")

    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Process a batch of texts to optimize token usage (simulated batching for now)."""
        # In a real-world scenario, we might combine these into a single prompt or use Claude's batch API
        results = []
        for text in texts:
            results.append(self.analyze_text(text))
        return results

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Comprehensive analysis using Claude AI.
        """
        if not text or not str(text).strip():
            return {
                "sentiment": "Neutral",
                "category": "Other",
                "topic": "General",
                "toxicity": 0.0,
                "emotion": "Neutral",
                "brand_perception": "Neutral",
                "risk_level": "Low"
            }

        # Step 1: Fast Language Detection (local)
        detected_lang = language_service.detect_language(text)

        if not self.client:
            return self._fallback_analysis(text, detected_lang)

        prompt = f"""
        Analyze the following social media text:
        "{text}"

        Provide a JSON response with:
        - "sentiment": "Positive", "Neutral", "Negative", or "Mixed"
        - "category": Broad category (e.g., Politics, Tech, Business, Entertainment)
        - "topic": Specific topic or keyword
        - "toxicity": Score from 0.0 to 1.0
        - "emotion": Dominant emotion (e.g., Joy, Anger, Fear, Sadness)
        - "intent": User intent (e.g., Feedback, Inquiry, Complaint, Praise)
        - "brand_perception": How the brand is perceived here (e.g., Trustworthy, Innovative, Poor Quality)
        - "risk_level": "Low", "Medium", "High" (based on reputation risk)

        Return ONLY valid JSON.
        """

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()
                
            result = json.loads(content)
            result["detected_language"] = detected_lang
            return result
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._fallback_analysis(text, detected_lang)

    def _fallback_analysis(self, text: str, language: str) -> Dict[str, Any]:
        """Basic fallback logic when AI is unavailable."""
        return {
            "sentiment": "Neutral",
            "category": "Other",
            "topic": "General",
            "toxicity": 0.0,
            "emotion": "Neutral",
            "brand_perception": "Neutral",
            "risk_level": "Low",
            "detected_language": language
        }

    def process_data_with_ai(self, platform: str, processed_filepath: str) -> str:
        """Enriches the processed data file with AI insights."""
        try:
            with open(processed_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            enriched_data = []
            for item in data:
                text = item.get("Text") or item.get("text") or ""
                ai_results = self.analyze_text(str(text))
                
                # Map results to standardized output format
                item["AiSentiment"] = ai_results.get("sentiment")
                item["DetectedLanguage"] = ai_results.get("detected_language")
                item["AiTopic"] = ai_results.get("topic")
                item["AiCategory"] = ai_results.get("category")
                item["RiskLevel"] = ai_results.get("risk_level")
                
                # Also keep lowercase keys for internal logic compatibility
                item["ai_sentiment"] = ai_results.get("sentiment")
                item["ai_category"] = ai_results.get("category")
                
                enriched_data.append(item)
                
            filename = processed_filepath.split("/")[-1].split("\\")[-1].replace(".json", "_enriched.json")
            enriched_filepath = storage_service.processed_dir / filename
            
            with open(enriched_filepath, 'w', encoding='utf-8') as f:
                json.dump(enriched_data, f, ensure_ascii=False, indent=2)
                
            return str(enriched_filepath)
        except Exception as e:
            logger.error(f"Enrichment error: {e}")
            raise e

ai_service = AIService()
