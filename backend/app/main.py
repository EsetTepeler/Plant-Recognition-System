from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api import plant_recognition, chatbot, health
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    New architecture: Kaggle + PlantNet + USDA + LLM
    """
    # Startup
    logger.info("Starting Plant Recognition System...")
    logger.info(" Architecture: Kaggle API + PlantNet + USDA (93K) + LLM")

    # Connect to Redis (optional - for caching and rate limiting)
    try:
        from app.services.redis_service import redis_service

        logger.info("Connecting to Redis...")
        await redis_service.connect()
        if redis_service.is_connected:
            logger.info("Redis connected - using distributed cache")
        else:
            logger.info("Redis not available - using in-memory fallback")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e} - using in-memory fallback")

    # Load USDA Plants Database
    try:
        from app.services.usda_service import usda_service

        count = usda_service.get_count()
        if count > 0:
            logger.info(f" USDA Weaviate: {count} plants available")
        else:
            logger.warning(" USDA not in Weaviate - run import_usda_to_weaviate.py")
    except Exception as e:
        logger.error(f"USDA service error: {e}")

    # Check Kaggle Notebook API
    try:
        from app.services.kaggle_notebook_service import kaggle_notebook_service

        if kaggle_notebook_service.notebook_url:
            logger.info(
                f" Kaggle API configured: {kaggle_notebook_service.notebook_url[:50]}..."
            )
        else:
            logger.warning(
                " Kaggle API not configured - image recognition may be limited"
            )
    except Exception as e:
        logger.error(f"Kaggle service error: {e}")

    # Check PlantNet API
    if settings.PLANTNET_API_KEY:
        logger.info(" PlantNet API configured")
    else:
        logger.warning(" PlantNet API key not set")

    # Check LLM API
    if settings.GOOGLE_AI_STUDIO_API_KEY:
        logger.info(" LLM: Google AI Studio (Gemini)")
    elif settings.OPENROUTER_API_KEY:
        logger.info(" LLM: OpenRouter")
    else:
        logger.warning(" No LLM API configured")

    logger.info("🌿 Application initialization completed")

    yield  # Application runs here

    # Shutdown
    logger.info("Shutting down application...")

    # Disconnect Redis
    try:
        from app.services.redis_service import redis_service

        await redis_service.disconnect()
        logger.info(" Redis disconnected")
    except Exception as e:
        logger.error(f"Redis disconnect error: {e}")

    logger.info(" Application shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="LLM-Supported Intelligent Plant Recognition System - Hybrid Architecture",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# GZip Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Routers
app.include_router(health.router, prefix=settings.API_V1_PREFIX, tags=["health"])
app.include_router(
    plant_recognition.router, prefix=settings.API_V1_PREFIX, tags=["recognition"]
)
app.include_router(chatbot.router, prefix=settings.API_V1_PREFIX, tags=["chatbot"])


@app.get("/")
async def root():
    return {
        "message": "Plant Recognition System API",
        "version": settings.VERSION,
        "architecture": "Hybrid: Kaggle + PlantNet + USDA + LLM",
        "docs": f"{settings.API_V1_PREFIX}/docs",
    }
