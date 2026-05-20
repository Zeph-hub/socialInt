from abc import ABC, abstractmethod
from app.orchestration.context import PipelineContext

class PipelineStage(ABC):
    name: str

    @abstractmethod
    async def execute(self, context: PipelineContext):
        """Execute the stage logic."""
        raise NotImplementedError
