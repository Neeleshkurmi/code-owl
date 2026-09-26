from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.core.config import settings
from app.api.routes.repositories import router as repositories_router
from app.api.routes.webhooks import router as webhook_router

app = FastAPI(title=settings.app_name)

app.include_router(health_router)
app.include_router(repositories_router)
app.include_router(webhook_router)

@app.get("/")
def root() :
    return {"message" : f"{settings.app_name} is running"}