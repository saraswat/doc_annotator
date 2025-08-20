import yaml
import os
import httpx
import json
import logging
from typing import Dict, List, AsyncGenerator, Optional, Any
from dataclasses import dataclass
from pathlib import Path

from ..schemas.chat import StreamingResponse

logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """Configuration for a specific LLM model"""
    technical_name: str
    common_name: str
    provider: str
    default_temperature: float = 0.7
    default_max_tokens: int = 2000

@dataclass
class ProviderConfig:
    """Configuration for an LLM provider"""
    type: str
    base_url: str
    api_key_env: str
    max_tokens_param: str = "max_tokens"

class UnifiedLLMService:
    """Unified service for all LLM providers and models"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "llms.yaml"
        
        self.config_path = config_path
        self.providers: Dict[str, ProviderConfig] = {}
        self.models: Dict[str, ModelConfig] = {}
        self.default_model: str = ""
        self.default_timeout: int = 60
        self._http_clients: Dict[str, httpx.AsyncClient] = {}
        
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
            
            # Load providers
            for provider_id, provider_data in config.get('providers', {}).items():
                self.providers[provider_id] = ProviderConfig(**provider_data)
            
            # Load models
            for model_id, model_data in config.get('models', {}).items():
                self.models[model_id] = ModelConfig(**model_data)
            
            # Load defaults
            self.default_model = config.get('default_model', '')
            self.default_timeout = config.get('default_timeout', 60)
            
            logger.info(f"Loaded {len(self.providers)} providers and {len(self.models)} models")
            
        except Exception as e:
            logger.error(f"Failed to load LLM configuration: {e}")
            raise
    
    def _get_http_client(self, provider_id: str) -> httpx.AsyncClient:
        """Get or create HTTP client for a provider"""
        if provider_id not in self._http_clients:
            provider = self.providers[provider_id]
            api_key = os.getenv(provider.api_key_env, "")
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # Add appropriate authorization header based on provider type
            if provider.type == "openai":
                headers["Authorization"] = f"Bearer {api_key}"
            elif provider.type == "anthropic":
                headers["x-api-key"] = api_key
            
            self._http_clients[provider_id] = httpx.AsyncClient(
                base_url=provider.base_url,
                headers=headers,
                timeout=self.default_timeout
            )
        
        return self._http_clients[provider_id]
    
    async def get_available_models(self) -> List[Dict[str, str]]:
        """Get list of available models with their common names"""
        available_models = []
        
        for model_id, model_config in self.models.items():
            provider = self.providers.get(model_config.provider)
            if provider and self._is_provider_available(provider):
                available_models.append({
                    "id": model_id,
                    "technical_name": model_config.technical_name,
                    "common_name": model_config.common_name,
                    "provider": model_config.provider
                })
        
        return available_models
    
    def _is_provider_available(self, provider: ProviderConfig) -> bool:
        """Check if a provider is available (has required API key)"""
        return bool(os.getenv(provider.api_key_env))
    
    def get_default_model_id(self) -> str:
        """Get the default model ID"""
        return self.default_model
    
    async def chat_completion(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None,
        stream: bool = False,
        **kwargs
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Generate chat completion for any model"""
        
        if model_id not in self.models:
            yield StreamingResponse(
                type="error",
                content="",
                error=f"Model '{model_id}' not found in configuration"
            )
            return
        
        model_config = self.models[model_id]
        provider_config = self.providers[model_config.provider]
        
        # Use model defaults if not provided
        if temperature is None:
            temperature = model_config.default_temperature
        if max_tokens is None:
            max_tokens = model_config.default_max_tokens
        
        try:
            if provider_config.type == "openai":
                async for response in self._openai_chat_completion(
                    model_config, provider_config, messages, temperature, max_tokens, stream, **kwargs
                ):
                    yield response
            elif provider_config.type == "anthropic":
                async for response in self._anthropic_chat_completion(
                    model_config, provider_config, messages, temperature, max_tokens, stream, **kwargs
                ):
                    yield response
            else:
                yield StreamingResponse(
                    type="error",
                    content="",
                    error=f"Unsupported provider type: {provider_config.type}"
                )
                
        except Exception as e:
            logger.error(f"Error in chat completion for {model_id}: {e}")
            yield StreamingResponse(
                type="error",
                content="",
                error=f"Chat completion error: {str(e)}"
            )
    
    async def _openai_chat_completion(
        self,
        model_config: ModelConfig,
        provider_config: ProviderConfig,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        stream: bool,
        **kwargs
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Handle OpenAI-style chat completion"""
        
        client = self._get_http_client(model_config.provider)
        
        # Prepare the payload
        payload = {
            "model": model_config.technical_name,
            "messages": messages,
            "temperature": temperature,
            provider_config.max_tokens_param: max_tokens,
            "stream": stream,
            **kwargs
        }
        
        try:
            if stream:
                async with client.stream("POST", "/v1/chat/completions", json=payload) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix
                            
                            if data.strip() == "[DONE]":
                                yield StreamingResponse(type="complete", content="")
                                break
                            
                            try:
                                chunk = json.loads(data)
                                if "choices" in chunk and len(chunk["choices"]) > 0:
                                    delta = chunk["choices"][0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield StreamingResponse(
                                            type="chunk",
                                            content=content,
                                            metadata={"model": model_config.technical_name}
                                        )
                                    
                                    # Check for completion
                                    finish_reason = chunk["choices"][0].get("finish_reason")
                                    if finish_reason:
                                        yield StreamingResponse(
                                            type="complete",
                                            content="",
                                            metadata={
                                                "finish_reason": finish_reason,
                                                "model": model_config.technical_name
                                            }
                                        )
                                        break
                            except json.JSONDecodeError:
                                continue
            else:
                response = await client.post("/v1/chat/completions", json=payload)
                response.raise_for_status()
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                yield StreamingResponse(
                    type="complete",
                    content=content,
                    metadata={
                        "model": model_config.technical_name,
                        "usage": data.get("usage", {})
                    }
                )
                
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = e.response.json().get("error", {}).get("message", str(e))
            except:
                error_detail = str(e)
            
            yield StreamingResponse(
                type="error",
                content="",
                error=f"HTTP {e.response.status_code}: {error_detail}"
            )
        except Exception as e:
            yield StreamingResponse(
                type="error",
                content="",
                error=str(e)
            )
    
    async def _anthropic_chat_completion(
        self,
        model_config: ModelConfig,
        provider_config: ProviderConfig,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        stream: bool,
        **kwargs
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Handle Anthropic-style chat completion"""
        
        client = self._get_http_client(model_config.provider)
        
        # Convert messages for Anthropic format (separate system message)
        system_message = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        payload = {
            "model": model_config.technical_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": anthropic_messages,
            **kwargs
        }
        
        if system_message:
            payload["system"] = system_message
        
        try:
            if stream:
                payload["stream"] = True
                async with client.stream("POST", "/v1/messages", json=payload) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            try:
                                chunk = json.loads(data)
                                if chunk.get("type") == "content_block_delta":
                                    content = chunk.get("delta", {}).get("text", "")
                                    if content:
                                        yield StreamingResponse(
                                            type="chunk",
                                            content=content
                                        )
                                elif chunk.get("type") == "message_stop":
                                    yield StreamingResponse(type="complete", content="")
                                    break
                            except json.JSONDecodeError:
                                continue
            else:
                response = await client.post("/v1/messages", json=payload)
                response.raise_for_status()
                
                data = response.json()
                content = data["content"][0]["text"] if data.get("content") else ""
                yield StreamingResponse(
                    type="complete",
                    content=content,
                    metadata={
                        "model": model_config.technical_name,
                        "usage": data.get("usage", {})
                    }
                )
                
        except Exception as e:
            yield StreamingResponse(
                type="error", 
                content="",
                error=str(e)
            )
    
    async def close(self):
        """Close all HTTP clients"""
        for client in self._http_clients.values():
            await client.aclose()

# Global instance
llm_service = UnifiedLLMService()

async def get_llm_service() -> UnifiedLLMService:
    """Get the global LLM service instance"""
    return llm_service