from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import os

class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"

@dataclass
class LLMProviderConfig:
    provider: LLMProvider
    api_key: str
    base_url: Optional[str] = None
    model: str = "gpt-4"
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

def get_llm_config(provider: str = "openai") -> LLMProviderConfig:
    """Get LLM configuration for the specified provider"""
    
    if provider == "openai":
        return LLMProviderConfig(
            provider=LLMProvider.OPENAI,
            api_key=os.getenv("OPENAI_API_KEY", "test-key"),
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "2000")),
        )
    elif provider == "anthropic":
        return LLMProviderConfig(
            provider=LLMProvider.ANTHROPIC,
            api_key=os.getenv("ANTHROPIC_API_KEY", "test-key"),
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
            temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "2000")),
        )
    elif provider == "custom":
        return LLMProviderConfig(
            provider=LLMProvider.CUSTOM,
            api_key=os.getenv("CUSTOM_API_KEY", "test-key"),
            base_url=os.getenv("CUSTOM_BASE_URL", "http://localhost:8000"),
            model=os.getenv("CUSTOM_MODEL", "custom-model"),
            temperature=float(os.getenv("CUSTOM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("CUSTOM_MAX_TOKENS", "2000")),
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")