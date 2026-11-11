import logging
import threading
import time

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import engine, get_db
from app.models import project_models, user_models
from app.routers import auth, payments, plans, projects

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="NakshaAI - AI-Powered Architectural Floor Plan & Building Map Generator with 2D/3D, Material Estimation, DXF/PDF Export, Auth, Credits & Monetization"
)

_auth_rate_paths = {
    f"{settings.API_V1_STR}/auth/login",
    f"{settings.API_V1_STR}/auth/register",
    f"{settings.API_V1_STR}/auth/password-reset/request",
}
_rate_buckets: dict[tuple[str, str], tuple[float, int]] = {}
_rate_lock = threading.Lock()


@app.middleware("http")
async def security_headers_and_rate_limit(request: Request, call_next):
    path = request.url.path
    if request.method == "POST" and path in _auth_rate_paths:
        client = request.client.host if request.client else "unknown"
        key = (client, path)
        now = time.time()
        with _rate_lock:
            window_start, count = _rate_buckets.get(key, (now, 0))
            if now - window_start >= 60:
                window_start, count = now, 0
            count += 1
            _rate_buckets[key] = (window_start, count)
        if count > settings.RATE_LIMIT_AUTH_PER_MINUTE:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={"Retry-After": "60"},
            )

    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if settings.is_production:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials="*" not in settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _ensure_transaction_columns():
    """create_all does not alter existing tables; add new columns safely."""
    try:
        insp = inspect(engine)
        if "transactions" not in insp.get_table_names():
            return
        cols = {c["name"] for c in insp.get_columns("transactions")}
        if "gateway_ref" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE transactions ADD COLUMN gateway_ref VARCHAR"))
    except Exception:
        pass


def _ensure_user_columns():
    """create_all does not alter existing user tables; add auth token columns safely."""
    try:
        insp = inspect(engine)
        if "users" not in insp.get_table_names():
            return
        cols = {c["name"] for c in insp.get_columns("users")}
        additions = {
            "reset_token_hash": "VARCHAR",
            "reset_token_expires": "TIMESTAMP",
            "verification_token_hash": "VARCHAR",
            "verification_token_expires": "TIMESTAMP",
            "is_verified": "BOOLEAN DEFAULT FALSE",
        }
        with engine.begin() as conn:
            for name, ddl in additions.items():
                if name not in cols:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {name} {ddl}"))
    except Exception:
        logger.exception("User table migration failed")


def _check_production_secrets():
    if not settings.is_production:
        return
    if settings.SECRET_KEY.startswith("nakshai-super-secret-key-change-in-production"):
        logger.warning("SECRET_KEY is still the default value. Set a strong SECRET_KEY in production.")
    if not settings.BACKEND_CORS_ORIGINS:
        logger.warning("BACKEND_CORS_ORIGINS is not set; using FRONTEND_URL for CORS.")


try:
    user_models.Base.metadata.create_all(bind=engine)
    project_models.Base.metadata.create_all(bind=engine)
    _ensure_transaction_columns()
    _ensure_user_columns()
except Exception:
    logger.exception("Database initialization failed")
_check_production_secrets()

app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(payments.router, prefix=settings.API_V1_STR)
app.include_router(plans.router, prefix=settings.API_V1_STR)
app.include_router(projects.router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "message": "NakshaAI Core API is running",
        "docs_url": "/docs",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
