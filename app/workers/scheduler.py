from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from app.utils.logger import log

class WorkerScheduler:
    def __init__(self):
        jobstores = {
            'default': MemoryJobStore()
        }
        self.scheduler = AsyncIOScheduler(jobstores=jobstores)

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            log.info("Worker scheduler started")

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            log.info("Worker scheduler stopped")

    def enqueue_pipeline(self, pipeline_func, execution, *args, **kwargs):
        """Enqueue a pipeline execution to run immediately in the background."""
        job_id = execution.pipeline_id
        
        # Prevent duplicate jobs
        if self.scheduler.get_job(job_id):
            log.warning("Job already exists", job_id=job_id)
            return job_id
            
        self.scheduler.add_job(
            pipeline_func,
            id=job_id,
            args=[execution, *args],
            kwargs=kwargs,
            misfire_grace_time=None
        )
        log.info("Pipeline job enqueued", job_id=job_id)
        return job_id

worker_scheduler = WorkerScheduler()
