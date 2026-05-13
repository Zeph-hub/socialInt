import logging
from typing import List, Optional, Dict
from langdetect import detect, detect_langs, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Ensure consistent results
DetectorFactory.seed = 0

logger = logging.getLogger(__name__)

class LanguageService:
    def detect_language(self, text: str) -> str:
        """Detect the primary language of the text."""
        if not text or not text.strip():
            return "unknown"
        
        try:
            return detect(text)
        except LangDetectException:
            return "unknown"
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return "unknown"

    def detect_with_confidence(self, text: str, threshold: float = 0.5) -> str:
        """Detect language and return 'unknown' if confidence is below threshold."""
        if not text or not text.strip():
            return "unknown"
            
        try:
            results = detect_langs(text)
            if not results:
                return "unknown"
            
            best = results[0]
            if best.prob >= threshold:
                return best.lang
            return "unknown"
        except LangDetectException:
            return "unknown"

    def batch_detect(self, texts: List[str]) -> List[str]:
        """Detect languages for a batch of texts."""
        return [self.detect_language(text) for text in texts]

language_service = LanguageService()
