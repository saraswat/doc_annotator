# Chat Service Setup Guide

This document explains how to configure the chat service for the Document Annotation System.

## Overview

The chat service supports multiple LLM providers and can be configured via environment variables. It supports:

- **OpenAI GPT Models** (GPT-4, GPT-3.5-turbo)
- **Anthropic Claude** (Claude 3 Sonnet, Haiku, Opus)
- **Custom LLM Services** (Ollama, vLLM, OpenAI-compatible APIs)

## Required Configuration

### 1. Environment Variables

Copy the `.env.example` file to `.env` and configure the required variables:

```bash
cd backend
cp .env.example .env
```

### 2. Choose Your LLM Provider

You need **at least one** LLM provider configured. The system will use the first available provider in this order:

#### Option A: OpenAI (Recommended)

1. Get an API key from [OpenAI Platform](https://platform.openai.com)
2. Add to `.env`:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
CHAT_DEFAULT_PROVIDER=openai
```

#### Option B: Anthropic Claude

1. Get an API key from [Anthropic Console](https://console.anthropic.com)
2. Add to `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
CHAT_DEFAULT_PROVIDER=anthropic
```

#### Option C: Custom LLM Service (Local/Self-hosted)

For services like Ollama, vLLM, or other OpenAI-compatible APIs:

```env
CUSTOM_LLM_API_KEY=your-api-token
CUSTOM_LLM_BASE_URL=http://localhost:11434/v1
CUSTOM_LLM_MODEL=llama2
CHAT_DEFAULT_PROVIDER=custom
```

## Configuration Reference

### Core Chat Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `CHAT_SERVICE_ENABLED` | Enable/disable chat functionality | `true` |
| `CHAT_DEFAULT_PROVIDER` | Default LLM provider to use | `openai` |

### OpenAI Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | *Required* |
| `OPENAI_BASE_URL` | OpenAI API base URL | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | Default OpenAI model | `gpt-4` |
| `OPENAI_TEMPERATURE` | Response creativity (0.0-2.0) | `0.7` |
| `OPENAI_MAX_TOKENS` | Maximum response length | `2000` |
| `OPENAI_TIMEOUT` | Request timeout (seconds) | `60` |

### Anthropic Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key | *Required* |
| `ANTHROPIC_BASE_URL` | Anthropic API base URL | `https://api.anthropic.com` |
| `ANTHROPIC_MODEL` | Default Claude model | `claude-3-sonnet-20240229` |
| `ANTHROPIC_TEMPERATURE` | Response creativity (0.0-1.0) | `0.7` |
| `ANTHROPIC_MAX_TOKENS` | Maximum response length | `2000` |
| `ANTHROPIC_TIMEOUT` | Request timeout (seconds) | `60` |

### Custom LLM Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `CUSTOM_LLM_API_KEY` | API key/token for custom service | `your-token` |
| `CUSTOM_LLM_BASE_URL` | Base URL of your LLM service | `http://localhost:11434/v1` |
| `CUSTOM_LLM_MODEL` | Model name to use | `llama2` |
| `CUSTOM_LLM_TEMPERATURE` | Response creativity | `0.7` |
| `CUSTOM_LLM_MAX_TOKENS` | Maximum response length | `2000` |
| `CUSTOM_LLM_TIMEOUT` | Request timeout (seconds) | `60` |

## Example Configurations

### Development Setup (OpenAI)

```env
# Basic chat setup with OpenAI
CHAT_SERVICE_ENABLED=true
CHAT_DEFAULT_PROVIDER=openai
OPENAI_API_KEY=sk-your-actual-openai-key
```

### Production Setup (Multiple Providers)

```env
# Enable multiple providers for redundancy
CHAT_SERVICE_ENABLED=true
CHAT_DEFAULT_PROVIDER=openai

# Primary provider
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4

# Backup provider
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
ANTHROPIC_MODEL=claude-3-sonnet-20240229
```

### Local Development (Ollama)

```env
# Use local Ollama instance
CHAT_SERVICE_ENABLED=true
CHAT_DEFAULT_PROVIDER=custom
CUSTOM_LLM_BASE_URL=http://localhost:11434/v1
CUSTOM_LLM_MODEL=llama2
CUSTOM_LLM_API_KEY=ollama
```

## Testing the Setup

1. Start the backend server:
   ```bash
   cd backend
   python main.py
   ```

2. Check the logs for LLM provider initialization:
   ```
   INFO:app.services.llm_client:OpenAI provider registered
   INFO:app.services.llm_client:LLM client initialized with 1 providers
   ```

3. Access the chat interface at `http://localhost:3000/chat`

## Troubleshooting

### "No LLM providers could be initialized"

- Ensure at least one provider has valid credentials
- Check that API keys are properly set (no quotes around values in .env)
- Verify network connectivity to the API endpoints

### "OpenAI API key is required but not configured"

- Set `OPENAI_API_KEY` in your `.env` file
- Or switch to a different provider using `CHAT_DEFAULT_PROVIDER`

### Chat interface shows but no responses

- Check backend logs for API errors
- Verify the selected model is available for your API key
- Test API key directly with curl or Postman

### Custom provider not working

- Ensure your custom service implements OpenAI-compatible endpoints
- Check that `CUSTOM_LLM_BASE_URL` is accessible from the backend
- Verify the model name exists in your custom service

## Security Notes

- **Never commit API keys** to version control
- Use environment-specific `.env` files
- Consider using secret management services in production
- Regularly rotate API keys
- Monitor usage and set billing limits

## API Key Sources

- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/settings/keys
- **Other providers**: Check their respective documentation

## Support

If you need help with chat setup:
1. Check the backend logs for specific error messages
2. Verify your API keys are valid and have sufficient credits
3. Test connectivity to the provider APIs
4. Ensure your `.env` file is properly formatted (no spaces around `=`)