"""
FastAPI Application Entry Point for Universal AI File Manager.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import get_settings
from backend.app.core.database import init_db
from backend.app.core.logging import logger

from backend.app.api.auth import router as auth_router
from backend.app.api.providers import router as providers_router
from backend.app.api.search import router as search_router
from backend.app.api.files import router as files_router
from backend.app.api.health import router as health_router
from backend.app.api.admin import router as admin_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Universal AI File Manager Backend...")
    # Initialize database tables
    await init_db()
    logger.info("Database initialized.")

    # Pre-index local files into ChromaDB vector store
    try:
        from backend.app.providers.local import LocalFileProvider
        from backend.app.services.indexing_service import semantic_search_service, DocumentExtractor
        local_prov = LocalFileProvider()
        files = await local_prov.list_files(limit=100)
        for f in files:
            file_path = local_prov.root_path / f.name
            if file_path.is_file():
                txt = DocumentExtractor.extract_text(file_path)
                if txt:
                    semantic_search_service.index_document(f, txt)
        logger.info(f"Indexed {len(files)} local documents into vector store.")
    except Exception as e:
        logger.warning(f"Initial document indexing note: {e}")

    yield
    logger.info("Shutting down Universal AI File Manager Backend...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Universal AI File Manager: An MCP-Based Platform for Intelligent Multi-Cloud File Search and Retrieval",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected server error occurred. Please try again later.",
            "path": request.url.path,
        },
    )

# Include Routers under /api
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(providers_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(files_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "Universal AI File Manager API is running",
        "documentation": "/docs",
        "health": "/api/health",
    }
