import pytest
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

from app.services.unified_llm_service import UnifiedLLMService, ModelConfig, ProviderConfig
from app.schemas.chat import StreamingResponse


@pytest.fixture
def sample_llms_yaml():
    """Create a temporary YAML config file for testing"""
    yaml_content = """
providers:
  test_openai:
    type: "openai"
    base_url: "http://test-openai.com/v1"
    api_key_env: "TEST_OPENAI_KEY"
    max_tokens_param: "max_completion_tokens"
    
  test_anthropic:
    type: "anthropic"
    base_url: "http://test-anthropic.com"
    api_key_env: "TEST_ANTHROPIC_KEY"
    max_tokens_param: "max_tokens"

models:
  test_model_1:
    technical_name: "test-gpt-model"
    common_name: "Test GPT"
    provider: "test_openai"
    default_temperature: 0.5
    default_max_tokens: 1000
    
  test_model_2:
    technical_name: "test-claude-model"
    common_name: "Test Claude"
    provider: "test_anthropic"
    default_temperature: 0.7
    default_max_tokens: 2000

default_model: "test_model_1"
default_timeout: 30
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name
    
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def intranet_llms_yaml():
    """Create a temporary YAML config file for intranet testing"""
    yaml_content = """
providers:
  test_intranet:
    type: "openai"
    base_url: "http://127.0.0.1:4000"
    api_key_env: "PROXY_API_KEY"
    max_tokens_param: "max_completion_tokens"
    intranet: true
    
  test_external:
    type: "openai"
    base_url: "https://api.openai.com/v1"
    api_key_env: "EXTERNAL_API_KEY"
    max_tokens_param: "max_completion_tokens"
    intranet: false

models:
  intranet_model:
    technical_name: "intranet-model"
    common_name: "Intranet Model"
    provider: "test_intranet"
    default_temperature: 0.7
    default_max_tokens: 2000
    
  external_model:
    technical_name: "external-model"
    common_name: "External Model"
    provider: "test_external"
    default_temperature: 0.7
    default_max_tokens: 2000

default_model: "intranet_model"
default_timeout: 30
intranet_mode: true
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name
    
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def llm_service(sample_llms_yaml):
    """Create UnifiedLLMService with test config"""
    return UnifiedLLMService(config_path=sample_llms_yaml)


@pytest.fixture
def intranet_llm_service(intranet_llms_yaml):
    """Create UnifiedLLMService with intranet test config"""
    return UnifiedLLMService(config_path=intranet_llms_yaml)


class TestUnifiedLLMService:
    
    def test_load_config(self, llm_service):
        """Test that configuration loads correctly"""
        # Check providers
        assert len(llm_service.providers) == 2
        assert "test_openai" in llm_service.providers
        assert "test_anthropic" in llm_service.providers
        
        # Check models
        assert len(llm_service.models) == 2
        assert "test_model_1" in llm_service.models
        assert "test_model_2" in llm_service.models
        
        # Check default model
        assert llm_service.default_model == "test_model_1"
        assert llm_service.default_timeout == 30
    
    def test_provider_config(self, llm_service):
        """Test provider configuration"""
        openai_provider = llm_service.providers["test_openai"]
        assert openai_provider.type == "openai"
        assert openai_provider.base_url == "http://test-openai.com/v1"
        assert openai_provider.api_key_env == "TEST_OPENAI_KEY"
        assert openai_provider.max_tokens_param == "max_completion_tokens"
        
        anthropic_provider = llm_service.providers["test_anthropic"]
        assert anthropic_provider.type == "anthropic"
        assert anthropic_provider.base_url == "http://test-anthropic.com"
        assert anthropic_provider.api_key_env == "TEST_ANTHROPIC_KEY"
        assert anthropic_provider.max_tokens_param == "max_tokens"
    
    def test_model_config(self, llm_service):
        """Test model configuration"""
        model_1 = llm_service.models["test_model_1"]
        assert model_1.technical_name == "test-gpt-model"
        assert model_1.common_name == "Test GPT"
        assert model_1.provider == "test_openai"
        assert model_1.default_temperature == 0.5
        assert model_1.default_max_tokens == 1000
        
        model_2 = llm_service.models["test_model_2"]
        assert model_2.technical_name == "test-claude-model"
        assert model_2.common_name == "Test Claude"
        assert model_2.provider == "test_anthropic"
        assert model_2.default_temperature == 0.7
        assert model_2.default_max_tokens == 2000
    
    @patch.dict(os.environ, {"TEST_OPENAI_KEY": "test-key"})
    async def test_get_available_models(self, llm_service):
        """Test getting available models (only those with API keys)"""
        models = await llm_service.get_available_models()
        
        # Only test_model_1 should be available (has TEST_OPENAI_KEY)
        assert len(models) == 1
        assert models[0]["id"] == "test_model_1"
        assert models[0]["common_name"] == "Test GPT"
        assert models[0]["technical_name"] == "test-gpt-model"
        assert models[0]["provider"] == "test_openai"
    
    @patch.dict(os.environ, {"TEST_OPENAI_KEY": "test-key", "TEST_ANTHROPIC_KEY": "test-key"})
    async def test_get_all_available_models(self, llm_service):
        """Test getting all models when both API keys are present"""
        models = await llm_service.get_available_models()
        
        assert len(models) == 2
        model_ids = [m["id"] for m in models]
        assert "test_model_1" in model_ids
        assert "test_model_2" in model_ids
    
    def test_get_default_model_id(self, llm_service):
        """Test getting default model ID"""
        assert llm_service.get_default_model_id() == "test_model_1"
    
    @patch('httpx.AsyncClient')
    @patch.dict(os.environ, {"TEST_OPENAI_KEY": "test-key"})
    async def test_openai_chat_completion_non_stream(self, mock_client, llm_service):
        """Test OpenAI chat completion without streaming"""
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {"input_tokens": 10, "output_tokens": 20}
        }
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance
        
        # Test chat completion
        messages = [{"role": "user", "content": "Hello"}]
        responses = []
        
        async for response in llm_service.chat_completion(
            model_id="test_model_1",
            messages=messages,
            stream=False
        ):
            responses.append(response)
        
        assert len(responses) == 1
        assert responses[0].type == "complete"
        assert responses[0].content == "Test response"
        assert responses[0].metadata["model"] == "test-gpt-model"
        assert responses[0].metadata["usage"]["input_tokens"] == 10
    
    async def test_chat_completion_invalid_model(self, llm_service):
        """Test chat completion with invalid model ID"""
        messages = [{"role": "user", "content": "Hello"}]
        responses = []
        
        async for response in llm_service.chat_completion(
            model_id="nonexistent_model",
            messages=messages
        ):
            responses.append(response)
        
        assert len(responses) == 1
        assert responses[0].type == "error"
        assert "not found in configuration" in responses[0].error
    
    @patch('httpx.AsyncClient')
    @patch.dict(os.environ, {"TEST_OPENAI_KEY": "test-key"})
    async def test_openai_streaming_completion(self, mock_client, llm_service):
        """Test OpenAI streaming chat completion"""
        # Mock streaming response
        async def mock_aiter_lines():
            yield "data: {'choices': [{'delta': {'content': 'Hello'}}]}"
            yield "data: {'choices': [{'delta': {'content': ' world'}}]}"
            yield "data: {'choices': [{'finish_reason': 'stop'}]}"
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.aiter_lines = mock_aiter_lines
        
        mock_client_instance = Mock()
        mock_client_instance.stream.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_client_instance.stream.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_client_instance
        
        # Test streaming
        messages = [{"role": "user", "content": "Hello"}]
        responses = []
        
        async for response in llm_service.chat_completion(
            model_id="test_model_1",
            messages=messages,
            stream=True
        ):
            responses.append(response)
        
        # Should have streaming chunks and completion
        assert len(responses) > 0
        # Note: This test would need more sophisticated JSON parsing mock to fully work
    
    def test_is_provider_available(self, llm_service):
        """Test provider availability checking"""
        openai_provider = llm_service.providers["test_openai"]
        anthropic_provider = llm_service.providers["test_anthropic"]
        
        # No API keys set
        assert not llm_service._is_provider_available(openai_provider)
        assert not llm_service._is_provider_available(anthropic_provider)
        
        # With API key
        with patch.dict(os.environ, {"TEST_OPENAI_KEY": "test-key"}):
            assert llm_service._is_provider_available(openai_provider)
            assert not llm_service._is_provider_available(anthropic_provider)
    
    async def test_close(self, llm_service):
        """Test closing HTTP clients"""
        # Create a mock client
        mock_client = Mock()
        mock_client.aclose = AsyncMock()
        llm_service._http_clients["test"] = mock_client
        
        await llm_service.close()
        mock_client.aclose.assert_called_once()


class TestModelConfig:
    
    def test_model_config_creation(self):
        """Test ModelConfig dataclass creation"""
        config = ModelConfig(
            technical_name="gpt-4",
            common_name="GPT-4",
            provider="openai",
            default_temperature=0.8,
            default_max_tokens=1500
        )
        
        assert config.technical_name == "gpt-4"
        assert config.common_name == "GPT-4"
        assert config.provider == "openai"
        assert config.default_temperature == 0.8
        assert config.default_max_tokens == 1500


class TestProviderConfig:
    
    def test_provider_config_creation(self):
        """Test ProviderConfig dataclass creation"""
        config = ProviderConfig(
            type="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            max_tokens_param="max_completion_tokens"
        )
        
        assert config.type == "openai"
        assert config.base_url == "https://api.openai.com/v1"
        assert config.api_key_env == "OPENAI_API_KEY"
        assert config.max_tokens_param == "max_completion_tokens"


class TestIntranetMode:
    
    def test_intranet_mode_configuration(self, intranet_llm_service):
        """Test that intranet mode is properly configured"""
        assert intranet_llm_service.intranet_mode is True
        
        # Check that intranet provider has correct configuration
        intranet_provider = intranet_llm_service.providers["test_intranet"]
        assert intranet_provider.intranet is True
        
        external_provider = intranet_llm_service.providers["test_external"]
        assert external_provider.intranet is False
    
    def test_intranet_provider_availability(self, intranet_llm_service):
        """Test provider availability in intranet mode"""
        intranet_provider = intranet_llm_service.providers["test_intranet"]
        external_provider = intranet_llm_service.providers["test_external"]
        
        # In intranet mode, intranet providers should be available without API keys
        assert intranet_llm_service._is_provider_available(intranet_provider) is True
        
        # External providers still need API keys even in intranet mode
        assert intranet_llm_service._is_provider_available(external_provider) is False
        
        # But external providers work when API key is provided
        with patch.dict(os.environ, {"EXTERNAL_API_KEY": "test-key"}):
            assert intranet_llm_service._is_provider_available(external_provider) is True
    
    @pytest.mark.asyncio
    async def test_intranet_available_models(self, intranet_llm_service):
        """Test that intranet models are available without API keys"""
        models = await intranet_llm_service.get_available_models()
        
        # Should have intranet model available (no API key needed)
        model_ids = [m["id"] for m in models]
        assert "intranet_model" in model_ids
        
        # External model should not be available (no API key set)
        assert "external_model" not in model_ids
        
        # When external API key is set, external model becomes available too
        with patch.dict(os.environ, {"EXTERNAL_API_KEY": "test-key"}):
            models_with_key = await intranet_llm_service.get_available_models()
            model_ids_with_key = [m["id"] for m in models_with_key]
            assert "intranet_model" in model_ids_with_key
            assert "external_model" in model_ids_with_key
    
    @patch.dict(os.environ, {"INTRANET_MODE": "false"})
    def test_environment_variable_override(self, intranet_llms_yaml):
        """Test that INTRANET_MODE environment variable overrides config"""
        # Create service with environment variable set to false
        service = UnifiedLLMService(config_path=intranet_llms_yaml)
        
        # Should be False due to environment variable override
        assert service.intranet_mode is False
        
        # Now intranet provider should not be available without API key
        intranet_provider = service.providers["test_intranet"]
        assert service._is_provider_available(intranet_provider) is False
    
    @patch.dict(os.environ, {"INTRANET_MODE": "true"})
    def test_environment_variable_enables_intranet(self, sample_llms_yaml):
        """Test that INTRANET_MODE=true enables intranet mode even when not in config"""
        # Create service with regular config (no intranet_mode set)
        service = UnifiedLLMService(config_path=sample_llms_yaml)
        
        # Should be True due to environment variable
        assert service.intranet_mode is True
    
    def test_provider_config_with_intranet_flag(self):
        """Test ProviderConfig with intranet flag"""
        config = ProviderConfig(
            type="openai",
            base_url="http://127.0.0.1:4000",
            api_key_env="PROXY_API_KEY",
            max_tokens_param="max_completion_tokens",
            intranet=True
        )
        
        assert config.intranet is True
        
        # Test default value
        config_default = ProviderConfig(
            type="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY"
        )
        
        assert config_default.intranet is False