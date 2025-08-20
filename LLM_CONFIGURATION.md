# LLM Configuration System

This system now uses a clean, configuration-driven approach for LLM providers and models. **No model names or provider names are hardcoded in the application code.**

## Architecture

### 1. Configuration File: `backend/config/llms.yaml`
- **Providers**: Define base URLs, API key environment variables, and provider-specific parameters
- **Models**: Define technical names, common names, default settings, and which provider to use
- **Default Model**: Specify which model to use by default
- **No Hardcoding**: The application code contains zero references to specific model or provider names

### 2. Unified LLM Service: `backend/app/services/unified_llm_service.py`
- **Single Interface**: One service handles all providers (OpenAI, Anthropic, custom endpoints)
- **Dynamic Loading**: Loads available models from YAML configuration
- **Provider Agnostic**: Uses the same chat completion interface for all providers
- **Automatic Parameter Handling**: Handles provider-specific parameters (e.g., `max_completion_tokens` vs `max_tokens`)

### 3. Dynamic Frontend: `frontend/src/components/Chat/ChatInput.tsx`
- **API-Driven Models**: Fetches available models from `/api/chat/models` endpoint
- **Dynamic Dropdown**: Populates model selection with common names from backend
- **No Hardcoding**: Contains no references to specific model names

## Configuration Example

```yaml
# backend/config/llms.yaml
providers:
  openai_proxy:
    type: "openai" 
    base_url: "http://127.0.0.1:4000"
    api_key_env: "PROXY_API_KEY"
    max_tokens_param: "max_completion_tokens"

models:
  o3_mini:
    technical_name: "o3_mini-2025-01-31-pyg-1"
    common_name: "O3 Mini"
    provider: "openai_proxy"
    default_temperature: 0.7
    default_max_tokens: 2000

default_model: "o3_mini"
```

## Environment Variables

Set only the API keys you need:

```bash
# For your intranet litellm proxy
export PROXY_API_KEY="dummy-key-for-litellm"

# For official OpenAI (optional)
export OPENAI_API_KEY="your-openai-key"

# For Anthropic (optional)  
export ANTHROPIC_API_KEY="your-anthropic-key"
```

## Adding New Models

To add a new model, just update `llms.yaml`:

1. **Add Provider** (if new):
```yaml
providers:
  new_provider:
    type: "openai"  # or "anthropic"
    base_url: "https://api.newprovider.com/v1"
    api_key_env: "NEW_PROVIDER_API_KEY"
```

2. **Add Model**:
```yaml
models:
  new_model:
    technical_name: "new-model-technical-name"
    common_name: "New Model"
    provider: "new_provider"
```

3. **Set Environment Variable**:
```bash
export NEW_PROVIDER_API_KEY="your-api-key"
```

The model will automatically appear in the frontend dropdown!

## API Endpoints

- **`GET /api/chat/models`**: Returns available models and default model
- **`POST /api/chat/sessions/{id}/messages`**: Uses model ID (not technical name) in settings

## Benefits

1. **Zero Hardcoding**: No model or provider names in application code
2. **Easy Configuration**: Add new models/providers by editing YAML file
3. **Environment Flexibility**: Same code works in different environments with different models
4. **Single Interface**: All LLM providers use the same API interface
5. **Dynamic UI**: Frontend automatically adapts to available models
6. **Provider Abstraction**: Switch between providers without code changes

## Migration Notes

- **Model IDs**: Use short IDs like `o3_mini`, not technical names like `o3_mini-2025-01-31-pyg-1`
- **No Max Tokens Issue**: System automatically handles `max_tokens` vs `max_completion_tokens`
- **Provider Independent**: Same chat completion interface works for all providers
- **Configuration Driven**: Everything is controlled by `llms.yaml`