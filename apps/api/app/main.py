"""Prestameami.pe API entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.errors import BusinessRuleError
from app.database import create_all
from app.routers import auth, clients, credits, dashboard, payments
from app.schemas.common import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Academic app: create the schema on boot instead of running migrations.
    create_all()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Gestion de microcreditos ('fiados') para bodegas. "
        "Metodo frances, base 360, montos en soles con 2 decimales."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(BusinessRuleError)
async def business_rule_handler(request: Request, exc: BusinessRuleError) -> JSONResponse:
    """Every domain error leaves through here with the same shape."""
    body = ErrorResponse(code=exc.code, message=exc.message, details=exc.details)
    return JSONResponse(status_code=exc.status_code, content=body.model_dump(mode="json"))


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Pydantic rejections get the same envelope so the frontend has one path."""
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(part) for part in first.get("loc", []) if part != "body")
    body = ErrorResponse(
        code="VALIDATION_ERROR",
        message=f"Revisa el campo '{field}': {first.get('msg', 'valor invalido')}.",
        details={
            "errors": [{"field": e.get("loc"), "message": e.get("msg")} for e in exc.errors()]
        },
    )
    return JSONResponse(status_code=422, content=body.model_dump(mode="json"))


app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(clients.router, prefix=settings.api_prefix)
app.include_router(credits.router, prefix=settings.api_prefix)
app.include_router(payments.router, prefix=settings.api_prefix)
app.include_router(payments.all_payments_router, prefix=settings.api_prefix)
app.include_router(dashboard.router, prefix=settings.api_prefix)


@app.get("/health", tags=["health"], summary="Estado del servicio")
def health() -> dict[str, str]:
    """Sirve para comprobar que la API esta levantada."""
    return {"status": "ok", "app": settings.app_name}
