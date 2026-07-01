import uvicorn
from app.api.routes import app
from app.config import get_settings

settings = get_settings()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower(),
        access_log=True,
    )
