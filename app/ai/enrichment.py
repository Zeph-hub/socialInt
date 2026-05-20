import asyncio
import json
from typing import Any, Dict, List
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.utils.logger import log

class AIEnrichmentClient:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None

    def _ensure_client(self):
        if not self.client:
            raise ValueError("Anthropic API key is not configured.")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def analyze_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self._ensure_client()
        
        # Prepare content for analysis
        prompt_data = []
        for i, item in enumerate(batch):
            content = item.get("content", "").strip()
            if content:
                prompt_data.append({"id": i, "text": content[:500]}) # Limit text length per item
        
        if not prompt_data:
            return batch
            
        system_prompt = (
            "You are a social media data analyst. Analyze the following list of posts. "
            "For each post, return a JSON object containing: "
            "'id' (must match the input id), 'language' (ISO 639-1 code), 'sentiment' (positive, negative, or neutral), "
            "'topics' (list of 1-3 main topics), and 'keywords' (list of 3-5 keywords). "
            "Return ONLY a JSON array of these objects."
        )
        
        user_prompt = f"Analyze these posts:\n{json.dumps(prompt_data, ensure_ascii=False)}"
        
        try:
            response = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1500,
                temperature=0.0,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            response_text = response.content[0].text
            
            # Find JSON array in the response
            start_idx = response_text.find("[")
            end_idx = response_text.rfind("]")
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx+1]
                analysis_results = json.loads(json_str)
                
                # Merge results back
                for result in analysis_results:
                    idx = result.get("id")
                    if idx is not None and 0 <= idx < len(batch):
                        batch[idx]["language"] = result.get("language")
                        batch[idx]["sentiment"] = result.get("sentiment")
                        batch[idx]["topics"] = result.get("topics", [])
                        batch[idx]["keywords"] = result.get("keywords", [])
                        batch[idx]["ai_enriched"] = True
            else:
                log.warning("AI response did not contain a valid JSON array")
                
        except Exception as e:
            log.error("AI batch analysis failed", error=str(e))
            raise
            
        return batch

    async def process_dataset(self, dataset: List[Dict[str, Any]], batch_size: int = 10) -> List[Dict[str, Any]]:
        log.info("Starting AI enrichment", total_records=len(dataset))
        enriched_dataset = []
        
        # Process in batches to avoid token limits
        for i in range(0, len(dataset), batch_size):
            batch = dataset[i:i+batch_size]
            try:
                enriched_batch = await self.analyze_batch(batch)
                enriched_dataset.extend(enriched_batch)
                log.debug("Processed batch", batch_index=i//batch_size, size=len(batch))
            except Exception as e:
                log.warning("Skipping batch due to error", batch_index=i//batch_size, error=str(e))
                # Append raw batch if enrichment fails completely for this batch
                enriched_dataset.extend(batch)
                
        log.info("AI enrichment completed")
        return enriched_dataset

ai_enrichment_client = AIEnrichmentClient()
