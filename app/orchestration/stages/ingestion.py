from app.orchestration.stages.base import PipelineStage
from app.orchestration.context import PipelineContext
from app.ingestion.apify import apify_client
from app.utils.logger import log

class IngestionStage(PipelineStage):
    name = "INGESTION"

    async def execute(self, context: PipelineContext):
        log.info("Starting ingestion", platform=context.platform, targets=context.targets)
        
        raw_data = await apify_client.fetch_data(
            platform=context.platform,
            targets=context.targets,
            posts_per_page=context.posts_per_page,
            comments_per_post=context.comments_per_post
        )
        
        if not raw_data:
            raise ValueError(f"No data returned from Apify for {context.platform}")
            
        context.raw_data = raw_data
        log.info("Ingestion completed", records_fetched=len(raw_data))
