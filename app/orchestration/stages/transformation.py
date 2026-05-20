from app.orchestration.stages.base import PipelineStage
from app.orchestration.context import PipelineContext
from app.processing.transformer import data_transformer
from app.utils.logger import log

class NormalizationStage(PipelineStage):
    name = "NORMALIZATION"

    async def execute(self, context: PipelineContext):
        if not context.raw_data:
            raise ValueError("No raw data available for normalization.")
            
        normalized_data = data_transformer.process(context.platform, context.raw_data)
        
        if not normalized_data:
            log.warning("Normalization resulted in empty dataset", pipeline_id=context.pipeline_id)
            
        context.normalized_data = normalized_data
        log.info("Normalization stage completed", records=len(normalized_data))
