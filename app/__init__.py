from fastapi import FastAPI
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
    
    # Dynamically include router to prevent startup crash while other project files are empty
    try:
        from app.api.routes import router as api_router
        app.include_router(api_router)
    except (ImportError, AttributeError):
        pass
        
    return app
