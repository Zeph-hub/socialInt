from typing import Any, Dict, List, Optional
from app.orchestration.models import PipelineExecution

class PipelineContext:
    def __init__(self, execution: PipelineExecution):
        self.execution = execution
        self.pipeline_id = execution.pipeline_id
        self.platform = execution.platform
        self.targets = execution.targets
        
        # Intermediate state
        self.raw_data: List[Dict[str, Any]] = []
        self.raw_filepath: Optional[str] = None
        
        self.normalized_data: List[Dict[str, Any]] = []
        self.enriched_data: List[Dict[str, Any]] = []
        self.processed_filepath: Optional[str] = None
        
        # Configuration
        self.posts_per_page: int = 100
        self.comments_per_post: int = 100
        
        # Settings
        self.skip_ai: bool = False
        
        # Store arbitrary metadata across stages
        self.metadata: Dict[str, Any] = {}
