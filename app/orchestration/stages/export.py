from app.orchestration.stages.base import PipelineStage
from app.orchestration.context import PipelineContext
from app.storage.manager import storage
from app.utils.logger import log

class ExportStage(PipelineStage):
    name = "EXPORT"

    async def execute(self, context: PipelineContext):
        data_to_save = context.enriched_data if context.enriched_data else context.normalized_data
        
        if not data_to_save:
            raise ValueError("No data to export.")
            
        filepath = storage.save_processed_data(
            platform=context.platform,
            data=data_to_save,
            pipeline_id=context.pipeline_id
        )
        
        context.processed_filepath = filepath
        log.info("Export completed", filepath=filepath, records=len(data_to_save))
