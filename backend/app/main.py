from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import documents, auth
from app.config import settings
from app.core.logging_config import logger

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
app.include_router(documents.router, prefix="/documents", tags=["Documentos"])


@app.on_event("startup")
async def startup_event():
    logger.info("Aplicación iniciada", extra={"extra_data": {"event": "startup"}})


@app.get("/")
def root():
    return {"status": "ok", "service": settings.app_name}


@app.get("/health")
def health_check():
    logger.info("Verificación de salud", extra={"extra_data": {"event": "health_check"}})
    return {"status": "healthy"}