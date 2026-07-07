import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
    
    # Configure CORS middleware for dashboard development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Dynamically include router to prevent startup crash while other project files are empty
    try:
        from app.api.routes import router as api_router
        app.include_router(api_router)
    except (ImportError, AttributeError):
        pass
        
    # Mount Vite production build directory if it exists
    dist_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dashboard", "dist")
    if os.path.exists(dist_path):
        app.mount("/", StaticFiles(directory=dist_path, html=True), name="static")
        
    return app
