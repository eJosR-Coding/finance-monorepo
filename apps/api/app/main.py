"""Punto de entrada de la API de Prestameami.pe."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import create_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    # App academica: creamos el esquema al arrancar en vez de usar migraciones.
    create_all()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Gestion de microcreditos ('fiados') para bodegas. Metodo frances, base 360.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}
