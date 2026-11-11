import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "NakshaAI Core API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://naksha-ai.vercel.app")
    BACKEND_CORS_ORIGINS: str = os.getenv("BACKEND_CORS_ORIGINS", "")
    RATE_LIMIT_AUTH_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_AUTH_PER_MINUTE", "30"))

    # LLM API Keys (Free Tiers Supported)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

    # Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "nakshai-super-secret-key-change-in-production-2026")
    
    # Payments
    STRIPE_SECRET_KEY: Optional[str] = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY: Optional[str] = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    JAZZCASH_MERCHANT_ID: Optional[str] = os.getenv("JAZZCASH_MERCHANT_ID", "")
    EASYPAISA_MERCHANT_ID: Optional[str] = os.getenv("EASYPAISA_MERCHANT_ID") or os.getenv("EASYPAYSA_MERCHANT_ID", "")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./nakshai.db")

    # Defaults
    DEFAULT_RATE_PKR_PER_SQFT: float = 3200.0  # Current standard grey structure rate
    PKR_TO_USD_RATE: float = 278.0

    @property
    def cors_origins(self) -> list[str]:
        raw = (self.BACKEND_CORS_ORIGINS or "").strip()
        if raw:
            return [origin.strip() for origin in raw.split(",") if origin.strip()]
        if self.ENVIRONMENT.lower() == "production":
            return [self.FRONTEND_URL.rstrip("/")]
        return ["*"]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
