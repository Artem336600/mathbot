"""FastAPI startup runner to integrate with asyncio loop."""
import asyncio
from loguru import logger
import uvicorn
from bot.config import settings

async def start_webapp():
    """Start uvicorn asynchronously inside existing event loop."""
    logger.info(f"[WEBAPP] Starting FastAPI server on port {settings.webapp_port}...")
    
    # We load app dynamically to avoid circular/early imports
    from webapp.main import app
    
    config = uvicorn.Config(
        app=app,
        host=settings.webapp_host,
        port=settings.webapp_port,
        log_level="warning", # uvicorn logs are quite noisy, let loguru handle ours
        use_colors=True,
    )
    server = uvicorn.Server(config)
    
    await server.serve()
