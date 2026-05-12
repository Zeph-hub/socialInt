import json
import logging
from typing import List, Dict, Any
import anthropic
from app.core.config import settings
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        api_key = settings.ANTHROPIC_API_KEY.strip()
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None

    def _ensure_client(self):
        if not self.client:
            raise ValueError("Anthropic API key is not configured. Please set ANTHROPIC_API_KEY in .env")

    def _fallback_analysis(self, text: str) -> Dict[str, Any]:
        lowered = (text or "").lower()
        positive = ("good", "great", "love", "excellent", "happy", "win", "best", "amazing")
        negative = ("bad", "hate", "angry", "poor", "fail", "worst", "broken", "sad")
        sentiment = "neutral"
        if any(word in lowered for word in positive):
            sentiment = "positive"
        if any(word in lowered for word in negative):
            sentiment = "negative"

        categories = {
            "politics": ("election", "government", "policy", "president", "minister", "vote"),
            "business": ("price", "market", "brand", "sales", "customer", "company"),
            "sports": ("game", "match", "team", "score", "league", "player"),
            "technology": ("ai", "app", "software", "phone", "data", "tech"),
            "entertainment": ("music", "movie", "show", "celebrity", "dance", "video"),
        }
        category = "other"
        for name, words in categories.items():
            if any(word in lowered for word in words):
                category = name
                break

        return {"language": "unknown", "sentiment": sentiment, "category": category}

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Uses Claude to detect language and classify the text.
        Returns a dictionary with 'language', 'sentiment', and 'category'.
        """
        if not text or not str(text).strip():
            return {"language": "unknown", "sentiment": "neutral", "category": "uncategorized"}
        if not self.client:
            return self._fallback_analysis(text)

        prompt = f"""
        Analyze the following social media text and provide a JSON response with three fields:
        - "language": The primary language of the text (e.g., "English", "Spanish", "French").
        - "sentiment": The sentiment of the text ("positive", "negative", or "neutral").
        - "category": The main topic category (e.g., "technology", "entertainment", "politics", "sports", "business", "lifestyle", "other").
        
        Text to analyze: "{text}"
        
        Return ONLY valid JSON.
        """

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            # Parse the JSON response from Claude
            # Claude sometimes wraps JSON in markdown blocks
            content = response.content[0].text
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()
                
            result = json.loads(content)
            return {
                "language": result.get("language", "unknown"),
                "sentiment": result.get("sentiment", "neutral"),
                "category": result.get("category", "uncategorized")
            }
        except anthropic.AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Error during AI analysis: {str(e)}")
            return {"language": "error", "sentiment": "error", "category": "error"}

    def _apply_analysis(self, item: Dict[str, Any], ai_results: Dict[str, Any]) -> Dict[str, Any]:
        detected_language = ai_results.get("language")
        language = item.get("ai_language") if detected_language in (None, "", "unknown") else detected_language
        language = language or "unknown"
        sentiment = ai_results.get("sentiment") or "neutral"
        category = ai_results.get("category") or "other"
        item["ai_language"] = language
        item["ai_sentiment"] = sentiment
        item["ai_category"] = category
        item["Ai-language"] = language
        item["Ai-sentiment"] = sentiment
        item["Ai-category"] = category
        return item

    def process_data_with_ai(self, platform: str, processed_filepath: str) -> str:
        """
        Loads already flattened (processed) data, runs AI analysis on text fields,
        and saves the enriched data back.
        """
        try:
            with open(processed_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            enriched_data = []
            # Determine the key for text based on platform or general structure
            for item in data:
                text = item.get("text") or item.get("description") or item.get("title") or item.get("content") or ""
                
                ai_results = self.analyze_text(str(text))
                item = self._apply_analysis(item, ai_results)
                
                enriched_data.append(item)
                
            # We can overwrite the processed file or create a new "enriched" file.
            # For simplicity, we overwrite the same file path or create a new one using storage_service
            # Let's create an "enriched" file to keep intermediate states
            filename = processed_filepath.split("/")[-1].split("\\")[-1].replace(".json", "_enriched.json")
            enriched_filepath = storage_service.processed_dir / filename
            
            with open(enriched_filepath, 'w', encoding='utf-8') as f:
                json.dump(enriched_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Successfully enriched {platform} data and saved to {enriched_filepath}")
            return str(enriched_filepath)
            
        except Exception as e:
            logger.error(f"Error in process_data_with_ai for {platform}: {str(e)}")
            raise e

ai_service = AIService()
