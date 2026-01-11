from fastapi import APIRouter
from datetime import datetime, UTC
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Comprehensive health check for all system components
    Architecture: Kaggle + PlantNet + USDA (Weaviate) + LLM
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": settings.VERSION,
        "services": {},
    }

    # USDA Plants Database check (Weaviate Cloud)
    try:
        from app.services.usda_service import usda_service

        count = usda_service.get_count()
        if count > 0:
            health_status["services"]["usda_plants"] = {
                "status": "healthy",
                "plant_count": count,
                "source": "Weaviate Cloud",
            }
        else:
            health_status["services"]["usda_plants"] = {
                "status": "not_loaded",
                "error": "Run import_usda_to_weaviate.py",
            }
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["usda_plants"] = {"status": "error", "error": str(e)}
        health_status["status"] = "degraded"

    # Kaggle Notebook API check
    try:
        from app.services.kaggle_notebook_service import kaggle_notebook_service

        if kaggle_notebook_service.notebook_url:
            health_status["services"]["kaggle"] = {
                "status": "configured",
                "url": kaggle_notebook_service.notebook_url[:50] + "...",
            }
        else:
            health_status["services"]["kaggle"] = {
                "status": "not_configured",
                "message": "Set KAGGLE_NOTEBOOK_URL in .env",
            }
    except Exception as e:
        health_status["services"]["kaggle"] = {"status": "error", "error": str(e)}

    # PlantNet API check
    if settings.PLANTNET_API_KEY:
        health_status["services"]["plantnet"] = {
            "status": "configured",
            "key_preview": settings.PLANTNET_API_KEY[:10] + "...",
        }
    else:
        health_status["services"]["plantnet"] = {
            "status": "not_configured",
            "message": "Set PLANTNET_API_KEY in .env",
        }

    # LLM check (GitHub Models GPT-5 > Gemini > Grok)
    if settings.GITHUB_TOKEN:
        health_status["services"]["llm"] = {
            "status": "configured",
            "provider": "GitHub Models GPT-5",
            "model": settings.GITHUB_MODELS_MODEL,
        }
    elif settings.GOOGLE_AI_STUDIO_API_KEY:
        health_status["services"]["llm"] = {
            "status": "configured",
            "provider": "Google Gemini",
        }
    elif settings.GROK_API_KEY:
        health_status["services"]["llm"] = {
            "status": "configured",
            "provider": "XAI Grok",
        }
    else:
        health_status["services"]["llm"] = {
            "status": "template_fallback",
            "message": "No LLM configured - using template responses",
        }

    # Redis check
    try:
        from app.services.redis_service import redis_service

        if redis_service.is_connected:
            health_status["services"]["redis"] = {"status": "connected"}
        else:
            health_status["services"]["redis"] = {
                "status": "not_connected",
                "message": "Using in-memory fallback",
            }
    except Exception as e:
        health_status["services"]["redis"] = {"status": "error", "error": str(e)}

    return health_status


@router.get("/status")
async def get_status():
    """Simple status endpoint"""
    return {"status": "ok", "timestamp": datetime.now(UTC).isoformat()}
