from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://annotation_user:annotation_pass@localhost:5432/annotation_db"
    DATABASE_TYPE: str = "postgresql"  # postgresql, mysql, or sqlite
    
    # Redis for caching and sessions
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security
    SECRET_KEY: str = "your-secret-key-generate-with-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OAuth Configuration
    OAUTH_PROVIDER: str = "google"
    OAUTH_CLIENT_ID: str = ""
    OAUTH_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_URI: str = "https://localhost:3000/auth/callback"
    
    # Google OAuth
    GOOGLE_DOMAIN: str = ""
    
    # Azure OAuth
    AZURE_TENANT_ID: str = ""
    
    # Okta OAuth
    OKTA_DOMAIN: str = ""
    
    # CORS - Allow all origins for intranet deployment
    CORS_ORIGINS: List[str] = ["*"]
    
    @classmethod
    def parse_cors_origins(cls, origins_str: str) -> List[str]:
        """Parse CORS origins from environment variable string"""
        import json
        try:
            return json.loads(origins_str)
        except:
            # Fallback to comma-separated parsing
            return [origin.strip() for origin in origins_str.split(',')]
    
    # File Storage
    STORAGE_TYPE: str = "local"
    UPLOAD_PATH: str = "./uploads"
    
    # S3 Configuration
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_BUCKET_NAME: str = "document-annotations"
    AWS_REGION: str = "us-east-1"
    
    # API Configuration
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Document Annotation System"
    
    # Initial Admin User
    ADMIN_USER_EMAIL: str = ""
    ADMIN_INITIAL_PASSWORD: str = ""
    
    # Chat Service Configuration
    CHAT_SERVICE_ENABLED: bool = True
    CHAT_DEFAULT_PROVIDER: str = "openai"
    
    # LLM Provider Configuration
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TIMEOUT: int = 60
    
    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com"
    ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"
    ANTHROPIC_TEMPERATURE: float = 0.7
    ANTHROPIC_MAX_TOKENS: int = 2000
    ANTHROPIC_TIMEOUT: int = 60
    
    # Custom LLM Service
    CUSTOM_LLM_API_KEY: str = ""
    CUSTOM_LLM_BASE_URL: str = ""
    CUSTOM_LLM_MODEL: str = ""
    CUSTOM_LLM_TEMPERATURE: float = 0.7
    CUSTOM_LLM_MAX_TOKENS: int = 2000
    CUSTOM_LLM_TIMEOUT: int = 60
    
    # Chat Service URLs and Endpoints
    CHAT_COMPLETION_ENDPOINT: str = "/chat/completions"
    CHAT_MODELS_ENDPOINT: str = "/models"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()