from app.orchestration.runner import PipelineRunner
from app.orchestration.context import PipelineContext
from app.orchestration.models import PipelineExecution
from app.orchestration.stages.ingestion import IngestionStage
from app.orchestration.stages.storage_stage import RawSaveStage
from app.orchestration.stages.transformation import NormalizationStage
from app.orchestration.stages.enrichment import AIEnrichmentStage
from app.orchestration.stages.export import ExportStage

def get_social_pipeline() -> PipelineRunner:
    """Returns a configured instance of the social intelligence pipeline."""
    return PipelineRunner(
        stages=[
            IngestionStage(),
            RawSaveStage(),
            NormalizationStage(),
            AIEnrichmentStage(),
            ExportStage()
        ]
    )

async def run_social_pipeline_async(execution: PipelineExecution, skip_ai: bool = False, posts_per_page: int = 100, comments_per_post: int = 100):
    context = PipelineContext(execution)
    context.skip_ai = skip_ai
    context.posts_per_page = posts_per_page
    context.comments_per_post = comments_per_post
    
    runner = get_social_pipeline()
    await runner.execute(context)
