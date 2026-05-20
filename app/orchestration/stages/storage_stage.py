from app.orchestration.stages.base import PipelineStage
from app.orchestration.context import PipelineContext
from app.storage.manager import storage
from app.utils.logger import log

class RawSaveStage(PipelineStage):
    name = "RAW_SAVE"

    async def execute(self, context: PipelineContext):
        if not context.raw_data:
            raise ValueError("No raw data to save in context.")
            
        filepath = storage.save_raw_payload(
            platform=context.platform,
            payload=context.raw_data,
            pipeline_id=context.pipeline_id
        )
        
        context.raw_filepath = filepath
        log.info("Raw data saved", filepath=filepath)
