from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import os

# Import settings from main config (avoid circular import)
def get_settings():
    from ..core.config import settings
    return settings

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"

@dataclass
class LLMProviderConfig:
    provider: LLMProvider
    api_key: str
    base_url: str
    model: str = "o3_mini"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 60
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        if self.provider == LLMProvider.OPENAI:
            return {"Authorization": f"Bearer {self.api_key}"}
        elif self.provider == LLMProvider.ANTHROPIC:
            return {"x-api-key": self.api_key}
        return {}

def get_llm_config(provider: str = None) -> LLMProviderConfig:
    """Get LLM configuration for the specified provider"""
    settings = get_settings()
    
    # Use default provider if none specified
    if provider is None:
        provider = settings.CHAT_DEFAULT_PROVIDER
    
    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is required but not configured in environment variables")
        return LLMProviderConfig(
            provider=LLMProvider.OPENAI,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
            timeout=settings.OPENAI_TIMEOUT
        )
    elif provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("Anthropic API key is required but not configured in environment variables")
        return LLMProviderConfig(
            provider=LLMProvider.ANTHROPIC,
            api_key=settings.ANTHROPIC_API_KEY,
            base_url=settings.ANTHROPIC_BASE_URL,
            model=settings.ANTHROPIC_MODEL,
            temperature=settings.ANTHROPIC_TEMPERATURE,
            max_tokens=settings.ANTHROPIC_MAX_TOKENS,
            timeout=settings.ANTHROPIC_TIMEOUT
        )
    elif provider == "custom":
        if not settings.CUSTOM_LLM_API_KEY or not settings.CUSTOM_LLM_BASE_URL:
            raise ValueError("Custom LLM API key and base URL are required but not configured")
        return LLMProviderConfig(
            provider=LLMProvider.CUSTOM,
            api_key=settings.CUSTOM_LLM_API_KEY,
            base_url=settings.CUSTOM_LLM_BASE_URL,
            model=settings.CUSTOM_LLM_MODEL or "default-model",
            temperature=settings.CUSTOM_LLM_TEMPERATURE,
            max_tokens=settings.CUSTOM_LLM_MAX_TOKENS,
            timeout=settings.CUSTOM_LLM_TIMEOUT
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}. Supported providers: openai, anthropic, custom")