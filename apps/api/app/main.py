"""Prestameami.pe API entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.bootstrap import bootstrap
from app.core.config import settings
from app.core.errors import BusinessRuleError, NotFoundError
from app.database import SessionLocal, create_all
from app.routers import auth, clients, credits, dashboard, payments
from app.schemas.common import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Academic app: create the schema on boot instead of running migrations.
    create_all()
    with SessionLocal() as session:
        bootstrap(session)
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


# ── Built frontend ─────────────────────────────────────────────────────────
# In a deploy the API also serves the compiled SPA, so there is one service,
# one URL and no CORS. Registered last: every /api route above wins first.
_dist = settings.web_dist_dir
if (_dist / "index.html").is_file():
    app.mount("/assets", StaticFiles(directory=_dist / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str) -> FileResponse:
        if full_path.startswith(settings.api_prefix.strip("/") + "/"):
            raise NotFoundError("NOT_FOUND", "La ruta solicitada no existe.")
        candidate = (_dist / full_path).resolve()
        if full_path and candidate.is_file() and candidate.is_relative_to(_dist.resolve()):
            return FileResponse(candidate)
        # Any client-side route (/clientes/3, /creditos/nuevo...) gets the SPA.
        return FileResponse(_dist / "index.html")
