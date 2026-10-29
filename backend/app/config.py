import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "NakshaAI Core API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # LLM API Keys (Free Tiers Supported)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY", "")

    # Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "nakshai-super-secret-key-change-in-production-2026")
    
    # Payments
    STRIPE_SECRET_KEY: Optional[str] = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY: Optional[str] = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    JAZZCASH_MERCHANT_ID: Optional[str] = os.getenv("JAZZCASH_MERCHANT_ID", "")
    EASYPAYSA_MERCHANT_ID: Optional[str] = os.getenv("EASYPAYSA_MERCHANT_ID", "")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./nakshai.db")

    # Defaults
    DEFAULT_RATE_PKR_PER_SQFT: float = 3200.0  # Current standard grey structure rate
    PKR_TO_USD_RATE: float = 278.0

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
