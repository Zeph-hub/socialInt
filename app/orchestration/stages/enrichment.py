from app.orchestration.stages.base import PipelineStage
from app.orchestration.context import PipelineContext
from app.ai.enrichment import ai_enrichment_client
from app.utils.logger import log

class AIEnrichmentStage(PipelineStage):
    name = "AI_ENRICHMENT"

    async def execute(self, context: PipelineContext):
        if context.skip_ai:
            log.info("Skipping AI Enrichment as requested", pipeline_id=context.pipeline_id)
            context.enriched_data = context.normalized_data
            return

        if not context.normalized_data:
            raise ValueError("No normalized data available for AI enrichment.")
            
        try:
            enriched_data = await ai_enrichment_client.process_dataset(context.normalized_data)
            context.enriched_data = enriched_data
            log.info("AI enrichment stage completed", records=len(enriched_data))
        except Exception as e:
            log.warning("AI enrichment failed completely, continuing with normalized data", error=str(e))
            context.enriched_data = context.normalized_data
