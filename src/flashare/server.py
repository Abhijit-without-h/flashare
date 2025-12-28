"""Main FastAPI server for Flashare."""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from flashare import __version__, __app_name__
from flashare.config import config
from flashare.api.routes import router as api_router
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    """
    # Startup
    print(f"🚀 Starting {__app_name__} v{__version__}")
    print(f"📁 Uploads directory: {config.uploads_dir}")
    
    yield
    
    # Shutdown
    print(f"👋 {__app_name__} shutting down")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title=__app_name__,
        version=__version__,
        description="CLI-First Hybrid File Sharing Tool",
        lifespan=lifespan,
    )
    
    # CORS middleware for browser access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    app.include_router(api_router)
    
    # Serve static files (mobile UI)
    static_dir = config.static_dir
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # Root route serves the mobile UI
    @app.get("/")
    async def serve_ui():
        """Serve the main mobile UI."""
        index_path = static_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        return {
            "app": __app_name__,
            "version": __version__,
            "message": "Welcome to Flashare! Mobile UI not found.",
            "api_docs": "/docs",
        }
    
    return app


# Create the default app instance
app = create_app()


def run_server(host: str | None = None, port: int | None = None):
    """
    Run the Flashare server.
    
    Args:
        host: Host to bind to. Defaults to config value.
        port: Port to bind to. Defaults to config value.
    """
    import uvicorn
    
    host = host or config.host
    port = port or config.port
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    run_server()
