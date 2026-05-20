from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class PipelineExecution(BaseModel):
    pipeline_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    platform: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    status: str = "pending" # pending, running, completed, failed
    failed_stage: Optional[str] = None
    records_processed: int = 0
    duration: Optional[float] = None
    error_message: Optional[str] = None
    targets: List[str] = []

    def mark_completed(self, records_processed: int):
        self.status = "completed"
        self.ended_at = datetime.utcnow()
        self.records_processed = records_processed
        self.duration = (self.ended_at - self.started_at).total_seconds()

    def mark_failed(self, stage: str, error: str):
        self.status = "failed"
        self.failed_stage = stage
        self.error_message = error
        self.ended_at = datetime.utcnow()
        self.duration = (self.ended_at - self.started_at).total_seconds()
