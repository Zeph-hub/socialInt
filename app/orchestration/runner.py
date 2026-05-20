import time
from typing import List
from app.utils.logger import log
from app.orchestration.context import PipelineContext
from app.orchestration.stages.base import PipelineStage
from app.storage.manager import storage

class PipelineRunner:
    def __init__(self, stages: List[PipelineStage]):
        self.stages = stages

    async def execute(self, context: PipelineContext):
        pipeline_id = context.pipeline_id
        
        log.info("Starting pipeline execution", pipeline_id=pipeline_id, platform=context.platform)
        
        context.execution.status = "running"
        storage.save_pipeline_metadata(pipeline_id, context.execution.model_dump())
        
        for stage in self.stages:
            stage_start_time = time.time()
            log.info("Starting stage", pipeline_id=pipeline_id, stage=stage.name)
            
            try:
                # Execute the stage
                await stage.execute(context)
                
                duration = time.time() - stage_start_time
                log.info("Stage completed successfully", pipeline_id=pipeline_id, stage=stage.name, duration=duration)
                
                # Persist state after each stage
                storage.save_pipeline_metadata(pipeline_id, context.execution.model_dump())
                
            except Exception as e:
                duration = time.time() - stage_start_time
                log.error("Stage failed", pipeline_id=pipeline_id, stage=stage.name, duration=duration, error=str(e))
                
                # Mark as failed and stop execution
                context.execution.mark_failed(stage=stage.name, error=str(e))
                storage.save_pipeline_metadata(pipeline_id, context.execution.model_dump())
                
                # We do not raise the exception so the pipeline doesn't crash the background worker,
                # but we stop further stages.
                return
                
        # If all stages complete successfully
        # Estimate records processed
        records = len(context.normalized_data) if context.normalized_data else 0
        context.execution.mark_completed(records_processed=records)
        storage.save_pipeline_metadata(pipeline_id, context.execution.model_dump())
        
        log.info("Pipeline execution completed", pipeline_id=pipeline_id, records=records, duration=context.execution.duration)
