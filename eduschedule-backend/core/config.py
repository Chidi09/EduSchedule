# eduschedule-backend/core/config.py
import os
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional

class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "EduSchedule"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_secret_change_in_production")

    # Security
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "jwt_secret_change_in_production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Database - Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # Redis & Celery
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", None) or os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", None) or os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_TIMEZONE: str = "UTC"

    # Email Configuration
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "noreply@eduschedule.name.ng")
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME", "EduSchedule")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "587"))
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.zeptomail.com")
    MAIL_STARTTLS: bool = os.getenv("MAIL_STARTTLS", "true").lower() == "true"
    MAIL_SSL_TLS: bool = os.getenv("MAIL_SSL_TLS", "false").lower() == "true"
    USE_CREDENTIALS: bool = os.getenv("USE_CREDENTIALS", "true").lower() == "true"
    VALIDATE_CERTS: bool = os.getenv("VALIDATE_CERTS", "true").lower() == "true"

    # Email Templates
    TEMPLATE_FOLDER: str = os.getenv("TEMPLATE_FOLDER", "templates")
    EMAIL_LOGO_URL: str = os.getenv("EMAIL_LOGO_URL", "https://eduschedule.name.ng/logo.png")
    COMPANY_ADDRESS: str = os.getenv("COMPANY_ADDRESS", "EduSchedule Nigeria, Lagos State, Nigeria")
    SUPPORT_EMAIL: str = os.getenv("SUPPORT_EMAIL", "support@eduschedule.name.ng")

    # API Security
    API_KEY_HEADER_NAME: str = "X-API-KEY"
    API_KEY_PREFIX: str = "edusk_"

    # CORS
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "https://eduschedule.name.ng,http://localhost:5173").split(",")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://eduschedule.name.ng")

    # Payment Configuration
    PAYSTACK_PUBLIC_KEY: str = os.getenv("PAYSTACK_PUBLIC_KEY", "")
    PAYSTACK_SECRET_KEY: str = os.getenv("PAYSTACK_SECRET_KEY", "")
    PAYSTACK_WEBHOOK_SECRET: str = os.getenv("PAYSTACK_WEBHOOK_SECRET", "")

    # AI Services
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Scheduler Configuration
    SCHEDULER_MAX_WORKERS: int = int(os.getenv("SCHEDULER_MAX_WORKERS", "3"))
    SCHEDULER_TIMEOUT_SECONDS: int = int(os.getenv("SCHEDULER_TIMEOUT_SECONDS", "300"))
    SOLUTION_LIMIT: int = int(os.getenv("SOLUTION_LIMIT", "5"))
    MAX_CONSECUTIVE_PERIODS: int = int(os.getenv("MAX_CONSECUTIVE_PERIODS", "4"))

    # Application Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    TESTING: bool = os.getenv("TESTING", "false").lower() == "true"

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")  # json or standard
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE", None)

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    RATE_LIMIT_BURST: int = int(os.getenv("RATE_LIMIT_BURST", "10"))

    # File Upload
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "./uploads")
    ALLOWED_EXTENSIONS: List[str] = os.getenv("ALLOWED_EXTENSIONS", "jpg,jpeg,png,gif,pdf,doc,docx").split(",")

    # External Services
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")

    # Monitoring & Analytics
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)
    ANALYTICS_ENABLED: bool = os.getenv("ANALYTICS_ENABLED", "false").lower() == "true"

    # Cache Settings
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes default
    CACHE_MAX_ENTRIES: int = int(os.getenv("CACHE_MAX_ENTRIES", "1000"))

    # Database Connection Pool
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "20"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))

    # Health Check
    HEALTH_CHECK_PATH: str = "/health"
    READINESS_CHECK_PATH: str = "/ready"

    # Task Queue Settings
    TASK_MAX_RETRIES: int = int(os.getenv("TASK_MAX_RETRIES", "3"))
    TASK_RETRY_DELAY: int = int(os.getenv("TASK_RETRY_DELAY", "60"))  # seconds
    TASK_SOFT_TIME_LIMIT: int = int(os.getenv("TASK_SOFT_TIME_LIMIT", "1800"))  # 30 minutes
    TASK_HARD_TIME_LIMIT: int = int(os.getenv("TASK_HARD_TIME_LIMIT", "3600"))  # 1 hour

    # Security Headers
    SECURE_COOKIES: bool = os.getenv("SECURE_COOKIES", "false").lower() == "true"
    HTTPS_ONLY: bool = os.getenv("HTTPS_ONLY", "false").lower() == "true"

    # Performance
    WORKER_CONNECTIONS: int = int(os.getenv("WORKER_CONNECTIONS", "1000"))
    WORKER_COUNT: int = int(os.getenv("WORKER_COUNT", "1"))

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"

    @property
    def is_testing(self) -> bool:
        return self.TESTING or self.ENVIRONMENT.lower() == "testing"

    def get_cors_origins(self) -> List[str]:
        """Get CORS origins as a list, filtering empty strings"""
        return [origin.strip() for origin in self.CORS_ORIGINS if origin.strip()]

    def get_database_url(self) -> str:
        """Construct database URL for external tools if needed"""
        return f"{self.SUPABASE_URL}/rest/v1/"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Create cached instance of settings"""
    return Settings()

# Convenience functions
def get_cors_origins() -> List[str]:
    return get_settings().get_cors_origins()

def is_production() -> bool:
    return get_settings().is_production

def is_development() -> bool:
    return get_settings().is_development
