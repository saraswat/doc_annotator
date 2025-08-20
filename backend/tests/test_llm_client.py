import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import AsyncGenerator

from app.services.llm_client import (
    LLMClient, 
    OpenAIProvider, 
    AnthropicProvider, 
    CustomEndpointProvider,
    LLMProviderError
)
from app.schemas.chat import StreamingResponse
from app.config.llm_config import LLMProviderConfig


@pytest.fixture
def mock_openai_config():
    """Mock OpenAI provider configuration"""
    return LLMProviderConfig(
        enabled=True,
        api_key="test-openai-key",
        base_url="https://api.openai.com/v1"
    )


@pytest.fixture
def mock_anthropic_config():
    """Mock Anthropic provider configuration"""
    return LLMProviderConfig(
        enabled=True,
        api_key="test-anthropic-key",
        base_url="https://api.anthropic.com"
    )


@pytest.fixture
def mock_custom_config():
    """Mock custom provider configuration"""
    return LLMProviderConfig(
        enabled=True,
        api_key="test-custom-key",
        base_url="https://custom-llm.example.com"
    )


class TestOpenAIProvider:
    """Test cases for OpenAI provider"""
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, mock_openai_config):
        """Test successful OpenAI provider initialization"""
        provider = OpenAIProvider(mock_openai_config)
        
        with patch('app.services.llm_client.openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.models.list = AsyncMock()
            mock_client_class.return_value = mock_client
            
            await provider.initialize()
            
            assert provider.client == mock_client
            mock_client_class.assert_called_once_with(
                api_key="test-openai-key",
                base_url="https://api.openai.com/v1"
            )
            mock_client.models.list.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_no_api_key(self, mock_openai_config):
        """Test OpenAI provider initialization without API key"""
        mock_openai_config.api_key = None
        provider = OpenAIProvider(mock_openai_config)
        
        with pytest.raises(LLMProviderError, match="OpenAI API key not provided"):
            await provider.initialize()
    
    @pytest.mark.asyncio
    async def test_initialize_connection_failed(self, mock_openai_config):
        """Test OpenAI provider initialization with connection failure"""
        provider = OpenAIProvider(mock_openai_config)
        
        with patch('app.services.llm_client.openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.models.list = AsyncMock(side_effect=Exception("Connection failed"))
            mock_client_class.return_value = mock_client
            
            with pytest.raises(LLMProviderError, match="Failed to initialize OpenAI provider"):
                await provider.initialize()
    
    @pytest.mark.asyncio
    async def test_chat_completion_streaming(self, mock_openai_config):
        """Test OpenAI chat completion with streaming"""
        provider = OpenAIProvider(mock_openai_config)
        
        # Mock streaming response
        mock_chunk1 = Mock()
        mock_chunk1.id = "chunk-1"
        mock_chunk1.choices = [Mock()]
        mock_chunk1.choices[0].delta = Mock()
        mock_chunk1.choices[0].delta.content = "Hello"
        mock_chunk1.choices[0].finish_reason = None
        
        mock_chunk2 = Mock()
        mock_chunk2.id = "chunk-2"
        mock_chunk2.choices = [Mock()]
        mock_chunk2.choices[0].delta = Mock()
        mock_chunk2.choices[0].delta.content = " world!"
        mock_chunk2.choices[0].finish_reason = None
        
        mock_chunk3 = Mock()
        mock_chunk3.id = "chunk-3"
        mock_chunk3.choices = [Mock()]
        mock_chunk3.choices[0].delta = Mock()
        mock_chunk3.choices[0].delta.content = None
        mock_chunk3.choices[0].finish_reason = "stop"
        
        async def mock_stream():
            yield mock_chunk1
            yield mock_chunk2
            yield mock_chunk3
        
        with patch('app.services.llm_client.openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_stream())
            mock_client_class.return_value = mock_client
            provider.client = mock_client
            
            messages = [{"role": "user", "content": "Hello"}]
            responses = []
            
            async for response in provider.chat_completion(
                messages=messages,
                model="gpt-4",
                stream=True
            ):
                responses.append(response)
            
            assert len(responses) == 3
            assert responses[0].type == "chunk"
            assert responses[0].content == "Hello"
            assert responses[1].type == "chunk"
            assert responses[1].content == " world!"
            assert responses[2].type == "complete"
    
    @pytest.mark.asyncio
    async def test_chat_completion_non_streaming(self, mock_openai_config):
        """Test OpenAI chat completion without streaming"""
        provider = OpenAIProvider(mock_openai_config)
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello, how can I help you?"
        mock_response.usage = Mock()
        mock_response.usage.dict = Mock(return_value={"total_tokens": 25})
        
        with patch('app.services.llm_client.openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            provider.client = mock_client
            
            messages = [{"role": "user", "content": "Hello"}]
            responses = []
            
            async for response in provider.chat_completion(
                messages=messages,
                model="gpt-4",
                stream=False
            ):
                responses.append(response)
            
            assert len(responses) == 1
            assert responses[0].type == "complete"
            assert responses[0].content == "Hello, how can I help you?"
            assert responses[0].metadata["usage"]["total_tokens"] == 25
    
    @pytest.mark.asyncio
    async def test_chat_completion_error(self, mock_openai_config):
        """Test OpenAI chat completion with error"""
        provider = OpenAIProvider(mock_openai_config)
        
        with patch('app.services.llm_client.openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
            mock_client_class.return_value = mock_client
            provider.client = mock_client
            
            messages = [{"role": "user", "content": "Hello"}]
            responses = []
            
            async for response in provider.chat_completion(
                messages=messages,
                model="gpt-4"
            ):
                responses.append(response)
            
            assert len(responses) == 1
            assert responses[0].type == "error"
            assert "API Error" in responses[0].error
    
    @pytest.mark.asyncio
    async def test_get_available_models(self, mock_openai_config):
        """Test getting available OpenAI models"""
        provider = OpenAIProvider(mock_openai_config)
        
        mock_models = Mock()
        mock_models.data = [
            Mock(id="gpt-4"),
            Mock(id="gpt-3.5-turbo"),
            Mock(id="text-davinci-003")
        ]
        
        with patch('app.services.llm_client.openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.models.list = AsyncMock(return_value=mock_models)
            mock_client_class.return_value = mock_client
            provider.client = mock_client
            
            models = await provider.get_available_models()
            
            assert "gpt-4" in models
            assert "gpt-3.5-turbo" in models
            assert "text-davinci-003" in models


class TestAnthropicProvider:
    """Test cases for Anthropic provider"""
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, mock_anthropic_config):
        """Test successful Anthropic provider initialization"""
        provider = AnthropicProvider(mock_anthropic_config)
        
        with patch('app.services.llm_client.AsyncAnthropic') as mock_client_class:
            await provider.initialize()
            
            mock_client_class.assert_called_once_with(
                api_key="test-anthropic-key",
                base_url="https://api.anthropic.com"
            )
    
    @pytest.mark.asyncio
    async def test_initialize_no_api_key(self, mock_anthropic_config):
        """Test Anthropic provider initialization without API key"""
        mock_anthropic_config.api_key = None
        provider = AnthropicProvider(mock_anthropic_config)
        
        with pytest.raises(LLMProviderError, match="Anthropic API key not provided"):
            await provider.initialize()
    
    @pytest.mark.asyncio
    async def test_chat_completion_streaming(self, mock_anthropic_config):
        """Test Anthropic chat completion with streaming"""
        provider = AnthropicProvider(mock_anthropic_config)
        
        with patch('app.services.llm_client.AsyncAnthropic') as mock_client_class:
            mock_client = AsyncMock()
            
            # Mock streaming context manager
            mock_stream_response = AsyncMock()
            mock_stream_response.__aenter__ = AsyncMock(return_value=mock_stream_response)
            mock_stream_response.__aexit__ = AsyncMock(return_value=None)
            
            # Mock text stream
            async def mock_text_stream():
                yield "Hello"
                yield " world!"
            
            mock_stream_response.text_stream = mock_text_stream()
            mock_stream_response.usage = Mock()
            mock_stream_response.usage.input_tokens = 10
            mock_stream_response.usage.output_tokens = 15
            
            mock_client.messages.stream = Mock(return_value=mock_stream_response)
            mock_client_class.return_value = mock_client
            provider.client = mock_client
            
            messages = [{"role": "user", "content": "Hello"}]
            responses = []
            
            async for response in provider.chat_completion(
                messages=messages,
                model="claude-3-sonnet-20240229",
                stream=True
            ):
                responses.append(response)
            
            assert len(responses) >= 2  # At least chunks + complete
            chunk_responses = [r for r in responses if r.type == "chunk"]
            complete_responses = [r for r in responses if r.type == "complete"]
            
            assert len(chunk_responses) >= 2
            assert len(complete_responses) == 1
            assert complete_responses[0].metadata["usage"]["input_tokens"] == 10
    
    @pytest.mark.asyncio
    async def test_get_available_models(self, mock_anthropic_config):
        """Test getting available Anthropic models"""
        provider = AnthropicProvider(mock_anthropic_config)
        
        models = await provider.get_available_models()
        
        assert "claude-3-opus-20240229" in models
        assert "claude-3-sonnet-20240229" in models
        assert "claude-3-haiku-20240307" in models


class TestCustomEndpointProvider:
    """Test cases for custom endpoint provider"""
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, mock_custom_config):
        """Test successful custom endpoint provider initialization"""
        provider = CustomEndpointProvider(mock_custom_config)
        
        with patch('app.services.llm_client.httpx.AsyncClient') as mock_client_class:
            await provider.initialize()
            
            mock_client_class.assert_called_once_with(
                base_url="https://custom-llm.example.com",
                headers={
                    "Authorization": "Bearer test-custom-key",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
    
    @pytest.mark.asyncio
    async def test_initialize_no_base_url(self, mock_custom_config):
        """Test custom endpoint provider initialization without base URL"""
        mock_custom_config.base_url = None
        provider = CustomEndpointProvider(mock_custom_config)
        
        with pytest.raises(LLMProviderError, match="Custom endpoint URL not provided"):
            await provider.initialize()
    
    @pytest.mark.asyncio
    async def test_chat_completion_streaming(self, mock_custom_config):
        """Test custom endpoint chat completion with streaming"""
        provider = CustomEndpointProvider(mock_custom_config)
        
        # Mock streaming response lines
        mock_lines = [
            "data: " + '{"choices": [{"delta": {"content": "Hello"}}]}',
            "data: " + '{"choices": [{"delta": {"content": " world!"}}]}',
            "data: [DONE]"
        ]
        
        with patch('app.services.llm_client.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.raise_for_status = Mock()
            
            # Mock aiter_lines
            async def mock_aiter_lines():
                for line in mock_lines:
                    yield line
            
            mock_response.aiter_lines = mock_aiter_lines
            mock_client.stream = AsyncMock()
            mock_client.stream.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_client.stream.return_value.__aexit__ = AsyncMock(return_value=None)
            
            mock_client_class.return_value = mock_client
            provider.http_client = mock_client
            
            messages = [{"role": "user", "content": "Hello"}]
            responses = []
            
            async for response in provider.chat_completion(
                messages=messages,
                model="custom-model",
                stream=True
            ):
                responses.append(response)
            
            chunk_responses = [r for r in responses if r.type == "chunk"]
            complete_responses = [r for r in responses if r.type == "complete"]
            
            assert len(chunk_responses) == 2
            assert chunk_responses[0].content == "Hello"
            assert chunk_responses[1].content == " world!"
            assert len(complete_responses) == 1


class TestLLMClient:
    """Test cases for main LLM client"""
    
    @pytest.mark.asyncio
    async def test_initialize_all_providers(self):
        """Test initializing LLM client with all providers"""
        client = LLMClient()
        
        with patch('app.services.llm_client.get_llm_config') as mock_get_config:
            mock_config = Mock()
            mock_config.openai = Mock(enabled=True, api_key="openai-key")
            mock_config.anthropic = Mock(enabled=True, api_key="anthropic-key")
            mock_config.custom = Mock(enabled=True, base_url="https://custom.com")
            mock_get_config.return_value = mock_config
            
            with patch.object(OpenAIProvider, 'initialize') as mock_openai_init, \
                 patch.object(AnthropicProvider, 'initialize') as mock_anthropic_init, \
                 patch.object(CustomEndpointProvider, 'initialize') as mock_custom_init:
                
                await client.initialize()
                
                mock_openai_init.assert_called_once()
                mock_anthropic_init.assert_called_once()
                mock_custom_init.assert_called_once()
                
                assert "openai" in client.providers
                assert "anthropic" in client.providers
                assert "custom" in client.providers
    
    @pytest.mark.asyncio
    async def test_initialize_no_providers(self):
        """Test initializing LLM client with no providers enabled"""
        client = LLMClient()
        
        with patch('app.services.llm_client.get_llm_config') as mock_get_config:
            mock_config = Mock()
            mock_config.openai = Mock(enabled=False)
            mock_config.anthropic = Mock(enabled=False)
            mock_config.custom = Mock(enabled=False)
            mock_get_config.return_value = mock_config
            
            with pytest.raises(LLMProviderError, match="No LLM providers could be initialized"):
                await client.initialize()
    
    def test_get_provider_for_model(self):
        """Test getting the correct provider for different models"""
        client = LLMClient()
        client.providers = {
            "openai": Mock(),
            "anthropic": Mock(),
            "custom": Mock()
        }
        
        # Test OpenAI models
        assert client.get_provider_for_model("gpt-4") == client.providers["openai"]
        assert client.get_provider_for_model("gpt-3.5-turbo") == client.providers["openai"]
        assert client.get_provider_for_model("text-davinci-003") == client.providers["openai"]
        
        # Test Anthropic models
        assert client.get_provider_for_model("claude-3-opus") == client.providers["anthropic"]
        assert client.get_provider_for_model("claude-3-sonnet") == client.providers["anthropic"]
        
        # Test custom models
        assert client.get_provider_for_model("custom-model") == client.providers["custom"]
        assert client.get_provider_for_model("unknown-model") == client.providers["custom"]
    
    @pytest.mark.asyncio
    async def test_chat_completion_with_provider(self):
        """Test chat completion routing to correct provider"""
        client = LLMClient()
        client._initialized = True
        
        mock_provider = AsyncMock()
        
        async def mock_completion(*args, **kwargs):
            yield StreamingResponse(type="chunk", content="Hello")
            yield StreamingResponse(type="complete", content="")
        
        mock_provider.chat_completion = mock_completion
        client.providers = {"openai": mock_provider}
        
        messages = [{"role": "user", "content": "Hello"}]
        responses = []
        
        async for response in client.chat_completion(
            messages=messages,
            model="gpt-4"
        ):
            responses.append(response)
        
        assert len(responses) == 2
        assert responses[0].type == "chunk"
        assert responses[0].content == "Hello"
        assert responses[1].type == "complete"
    
    @pytest.mark.asyncio
    async def test_chat_completion_no_provider(self):
        """Test chat completion when no provider is available"""
        client = LLMClient()
        client._initialized = True
        client.providers = {}
        
        messages = [{"role": "user", "content": "Hello"}]
        responses = []
        
        async for response in client.chat_completion(
            messages=messages,
            model="gpt-4"
        ):
            responses.append(response)
        
        assert len(responses) == 1
        assert responses[0].type == "error"
        assert "No provider available" in responses[0].error
    
    @pytest.mark.asyncio
    async def test_get_available_models(self):
        """Test getting available models from all providers"""
        client = LLMClient()
        client._initialized = True
        
        mock_openai_provider = AsyncMock()
        mock_openai_provider.get_available_models = AsyncMock(return_value=["gpt-4", "gpt-3.5-turbo"])
        
        mock_anthropic_provider = AsyncMock()
        mock_anthropic_provider.get_available_models = AsyncMock(return_value=["claude-3-opus", "claude-3-sonnet"])
        
        client.providers = {
            "openai": mock_openai_provider,
            "anthropic": mock_anthropic_provider
        }
        
        models = await client.get_available_models()
        
        assert models["openai"] == ["gpt-4", "gpt-3.5-turbo"]
        assert models["anthropic"] == ["claude-3-opus", "claude-3-sonnet"]


@pytest.mark.asyncio
class TestLLMClientIntegration:
    """Integration tests for LLM client"""
    
    async def test_end_to_end_conversation(self):
        """Test end-to-end conversation flow"""
        client = LLMClient()
        
        # Mock a successful provider initialization and conversation
        with patch('app.services.llm_client.get_llm_config') as mock_get_config:
            mock_config = Mock()
            mock_config.openai = Mock(enabled=True, api_key="test-key")
            mock_config.anthropic = Mock(enabled=False)
            mock_config.custom = Mock(enabled=False)
            mock_get_config.return_value = mock_config
            
            with patch.object(OpenAIProvider, 'initialize'):
                await client.initialize()
                
                # Mock provider response
                mock_provider = client.providers["openai"]
                
                async def mock_completion(*args, **kwargs):
                    yield StreamingResponse(type="chunk", content="I")
                    yield StreamingResponse(type="chunk", content=" can")
                    yield StreamingResponse(type="chunk", content=" help")
                    yield StreamingResponse(type="chunk", content=" you!")
                    yield StreamingResponse(type="complete", content="", metadata={"usage": {"total_tokens": 20}})
                
                mock_provider.chat_completion = mock_completion
                
                messages = [{"role": "user", "content": "Can you help me?"}]
                full_response = ""
                
                async for response in client.chat_completion(
                    messages=messages,
                    model="gpt-4",
                    temperature=0.7,
                    stream=True
                ):
                    if response.type == "chunk":
                        full_response += response.content
                    elif response.type == "complete":
                        assert response.metadata["usage"]["total_tokens"] == 20
                
                assert full_response == "I can help you!"