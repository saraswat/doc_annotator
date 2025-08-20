from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, Optional, List
import asyncio
import json
import logging
from datetime import datetime

import httpx
import openai
from anthropic import Anthropic, AsyncAnthropic

from ..config.llm_config import LLMProviderConfig, get_llm_config
from ..schemas.chat import StreamingResponse

logger = logging.getLogger(__name__)

class LLMProviderError(Exception):
    """Custom exception for LLM provider errors"""
    pass

class BaseLLMProvider(ABC):
    """Base class for all LLM providers"""
    
    def __init__(self, config: LLMProviderConfig):
        self.config = config
        self.client = None
        
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider with necessary credentials"""
        pass
        
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        **kwargs
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Generate chat completion with streaming support"""
        pass
        
    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """Get list of available models for this provider"""
        pass

class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider"""
    
    async def initialize(self) -> None:
        if not self.config.api_key:
            raise LLMProviderError("OpenAI API key not provided")
            
        self.client = openai.AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url or "https://api.openai.com/v1"
        )
        
        # Test the connection
        try:
            await self.client.models.list()
            logger.info("OpenAI provider initialized successfully")
        except Exception as e:
            raise LLMProviderError(f"Failed to initialize OpenAI provider: {str(e)}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        **kwargs
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Generate OpenAI chat completion with streaming"""
        try:
            # Convert our message format to OpenAI format
            openai_messages = [
                {"role": msg["role"], "content": msg["content"]} 
                for msg in messages
            ]
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs
            )
            
            if stream:
                async for chunk in response:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, 'content') and delta.content:
                            yield StreamingResponse(
                                type="chunk",
                                content=delta.content,
                                metadata={"chunk_id": chunk.id}
                            )
                        
                        # Check for completion
                        if chunk.choices[0].finish_reason:
                            yield StreamingResponse(
                                type="complete",
                                content="",
                                metadata={
                                    "finish_reason": chunk.choices[0].finish_reason,
                                    "model": model,
                                    "usage": getattr(chunk, 'usage', None)
                                }
                            )
                            break
            else:
                content = response.choices[0].message.content
                yield StreamingResponse(
                    type="complete",
                    content=content,
                    metadata={
                        "model": model,
                        "usage": response.usage.dict() if response.usage else None
                    }
                )
                
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            yield StreamingResponse(
                type="error",
                content="",
                error=f"OpenAI API error: {str(e)}"
            )
    
    async def get_available_models(self) -> List[str]:
        """Get available OpenAI models"""
        try:
            models = await self.client.models.list()
            gpt_models = [
                model.id for model in models.data 
                if 'gpt' in model.id.lower()
            ]
            return sorted(gpt_models)
        except Exception as e:
            logger.error(f"Failed to fetch OpenAI models: {str(e)}")
            return ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo']  # Fallback

class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider"""
    
    async def initialize(self) -> None:
        if not self.config.api_key:
            raise LLMProviderError("Anthropic API key not provided")
            
        self.client = AsyncAnthropic(
            api_key=self.config.api_key,
            base_url=self.config.base_url or "https://api.anthropic.com"
        )
        
        logger.info("Anthropic provider initialized successfully")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        **kwargs
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Generate Anthropic chat completion with streaming"""
        try:
            # Convert messages for Anthropic format
            # Anthropic expects system message separate from user/assistant messages
            system_message = ""
            claude_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    claude_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            kwargs_clean = {k: v for k, v in kwargs.items() if k not in ['stream']}
            
            if stream:
                async with self.client.messages.stream(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_message if system_message else None,
                    messages=claude_messages,
                    **kwargs_clean
                ) as stream_response:
                    async for text in stream_response.text_stream:
                        yield StreamingResponse(
                            type="chunk",
                            content=text
                        )
                    
                    # Send completion signal
                    yield StreamingResponse(
                        type="complete",
                        content="",
                        metadata={
                            "model": model,
                            "usage": {
                                "input_tokens": stream_response.usage.input_tokens,
                                "output_tokens": stream_response.usage.output_tokens
                            } if hasattr(stream_response, 'usage') else None
                        }
                    )
            else:
                response = await self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_message if system_message else None,
                    messages=claude_messages,
                    **kwargs_clean
                )
                
                content = response.content[0].text if response.content else ""
                yield StreamingResponse(
                    type="complete",
                    content=content,
                    metadata={
                        "model": model,
                        "usage": {
                            "input_tokens": response.usage.input_tokens,
                            "output_tokens": response.usage.output_tokens
                        } if response.usage else None
                    }
                )
                
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            yield StreamingResponse(
                type="error",
                content="",
                error=f"Anthropic API error: {str(e)}"
            )
    
    async def get_available_models(self) -> List[str]:
        """Get available Anthropic models"""
        # Anthropic doesn't have a models endpoint, return known models
        return [
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229',
            'claude-3-haiku-20240307',
            'claude-3-5-sonnet-20241022'
        ]

class CustomEndpointProvider(BaseLLMProvider):
    """Custom OpenAI-compatible endpoint provider"""
    
    async def initialize(self) -> None:
        if not self.config.base_url:
            raise LLMProviderError("Custom endpoint URL not provided")
        
        # Initialize httpx client for custom endpoints
        self.http_client = httpx.AsyncClient(
            base_url=self.config.base_url,
            headers={
                "Authorization": f"Bearer {self.config.api_key}" if self.config.api_key else {},
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
        
        logger.info(f"Custom endpoint provider initialized: {self.config.base_url}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        **kwargs
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Generate completion using custom OpenAI-compatible endpoint"""
        try:
            payload = {
                "model": model,
                "messages": [{"role": msg["role"], "content": msg["content"]} for msg in messages],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream,
                **kwargs
            }
            
            if stream:
                async with self.http_client.stream(
                    "POST", "/v1/chat/completions", json=payload
                ) as response:
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
                                            content=content
                                        )
                            except json.JSONDecodeError:
                                continue
            else:
                response = await self.http_client.post("/v1/chat/completions", json=payload)
                response.raise_for_status()
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                yield StreamingResponse(
                    type="complete",
                    content=content,
                    metadata={"model": model}
                )
                
        except Exception as e:
            logger.error(f"Custom endpoint error: {str(e)}")
            yield StreamingResponse(
                type="error",
                content="",
                error=f"Custom endpoint error: {str(e)}"
            )
    
    async def get_available_models(self) -> List[str]:
        """Get available models from custom endpoint"""
        try:
            response = await self.http_client.get("/v1/models")
            response.raise_for_status()
            
            data = response.json()
            return [model["id"] for model in data.get("data", [])]
        except Exception as e:
            logger.error(f"Failed to fetch custom endpoint models: {str(e)}")
            return ["custom-model"]  # Fallback

class LLMClient:
    """Main LLM client that manages multiple providers"""
    
    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self._initialized = False
        # Import settings here to avoid circular imports
        from ..core.config import settings
        self.settings = settings
    
    async def initialize(self) -> None:
        """Initialize all configured providers"""
        if self._initialized:
            return
        
        # Initialize OpenAI provider if API key is available
        if self.settings.OPENAI_API_KEY:
            try:
                config = get_llm_config("openai")
                provider = OpenAIProvider(config)
                await provider.initialize()
                self.providers["openai"] = provider
                logger.info("OpenAI provider registered")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI provider: {str(e)}")
        
        # Initialize Anthropic provider if API key is available
        if self.settings.ANTHROPIC_API_KEY:
            try:
                config = get_llm_config("anthropic")
                provider = AnthropicProvider(config)
                await provider.initialize()
                self.providers["anthropic"] = provider
                logger.info("Anthropic provider registered")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic provider: {str(e)}")
        
        # Initialize custom endpoint provider if configured
        if self.settings.CUSTOM_LLM_API_KEY and self.settings.CUSTOM_LLM_BASE_URL:
            try:
                config = get_llm_config("custom")
                provider = CustomEndpointProvider(config)
                await provider.initialize()
                self.providers["custom"] = provider
                logger.info("Custom endpoint provider registered")
            except Exception as e:
                logger.error(f"Failed to initialize custom endpoint provider: {str(e)}")
        
        if not self.providers:
            raise LLMProviderError("No LLM providers could be initialized")
        
        self._initialized = True
        logger.info(f"LLM client initialized with {len(self.providers)} providers")
    
    def get_default_provider(self) -> Optional[BaseLLMProvider]:
        """Get the default provider based on configuration"""
        default_provider_name = self.settings.CHAT_DEFAULT_PROVIDER
        provider = self.providers.get(default_provider_name)
        
        # Fallback to first available provider if default is not available
        if not provider and self.providers:
            provider = next(iter(self.providers.values()))
        
        return provider
    
    def get_provider_for_model(self, model: str) -> Optional[BaseLLMProvider]:
        """Get the appropriate provider for a given model"""
        if model.startswith(("gpt-", "text-", "davinci", "curie", "babbage", "ada")):
            return self.providers.get("openai")
        elif model.startswith(("claude-")):
            return self.providers.get("anthropic")
        else:
            # Try custom provider first, then default, then any available
            return (self.providers.get("custom") or 
                   self.get_default_provider())
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        **kwargs
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Generate chat completion using the appropriate provider"""
        if not self._initialized:
            await self.initialize()
        
        provider = self.get_provider_for_model(model)
        if not provider:
            yield StreamingResponse(
                type="error",
                content="",
                error=f"No provider available for model: {model}"
            )
            return
        
        async for response in provider.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **kwargs
        ):
            yield response
    
    async def get_available_models(self) -> Dict[str, List[str]]:
        """Get all available models from all providers"""
        if not self._initialized:
            await self.initialize()
        
        models = {}
        for name, provider in self.providers.items():
            try:
                provider_models = await provider.get_available_models()
                models[name] = provider_models
            except Exception as e:
                logger.error(f"Failed to get models for {name}: {str(e)}")
                models[name] = []
        
        return models

# Global client instance
llm_client = LLMClient()

async def get_llm_client() -> LLMClient:
    """Get the global LLM client instance"""
    if not llm_client._initialized:
        await llm_client.initialize()
    return llm_client