from fastapi import FastAPI
from app.api.routes import router as api_router
from app.config import settings

def create_app() -> FastAPI:
    """
    FastAPI application factory.
    """
    app = FastAPI(
        title="GitHub PR Review Assistant",
        description="An AI-powered PR reviewer",
        version="1.0.0",
        debug=settings.debug
    )
    
    app.include_router(api_router)
    
    return app
