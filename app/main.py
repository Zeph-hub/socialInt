from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.routers import admin, analysis, files, ingestion, powerbi, monitoring, analytics
from app.workers.scheduler import worker_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the background scheduler
    worker_scheduler.start()
    yield
    # Shutdown: Stop the scheduler gracefully
    worker_scheduler.stop()

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan
    )

    # Set all CORS enabled origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    frontend_dir = "app/frontend"
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def root():
        return RedirectResponse("http://0.0.0.0:3000")
        
    # Include routers here
    app.include_router(ingestion.router, prefix=settings.API_V1_STR)
    app.include_router(analysis.router, prefix=settings.API_V1_STR)
    app.include_router(powerbi.router, prefix=settings.API_V1_STR)
    app.include_router(files.router, prefix=settings.API_V1_STR)
    app.include_router(admin.router, prefix=settings.API_V1_STR)
    app.include_router(monitoring.router, prefix=settings.API_V1_STR)
    app.include_router(analytics.router, prefix=settings.API_V1_STR)

    return app

app = create_app()
