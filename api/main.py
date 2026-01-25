from fastapi import FastAPI
from fastapi.responses import JSONResponse
from scalar_fastapi import get_scalar_api_reference
from contextlib import asynccontextmanager

from core.config import settings
from core.cosmos import cosmos_client
from routers import webhooks, conversations, profiles, calls


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup: Initialize Cosmos DB containers
    await cosmos_client.initialize_containers()
    yield
    # Shutdown: cleanup if needed
    pass


app = FastAPI(
    title=settings.app_name,
    description="API for processing Holly (ElevenLabs) conversation webhooks",
    version=settings.app_version,
    debug=settings.debug,
    docs_url=None,  # Disable default Swagger UI
    redoc_url=None,  # Disable ReDoc
    lifespan=lifespan
)

# Include routers
app.include_router(webhooks.router)
app.include_router(conversations.router)
app.include_router(profiles.router)
app.include_router(calls.router)


@app.get("/docs", include_in_schema=False)
async def scalar_docs():
    """Scalar API documentation"""
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "holly-and-morty-api"
        }
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Holly and Morty API",
        "docs": "/docs",
        "health": "/health",
        "webhooks": {
            "holly_conversation": "/webhooks/holly-conversation"
        }
    }
