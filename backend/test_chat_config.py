#!/usr/bin/env python3
"""Test script to verify chat configuration"""

from app.config.llm_config import get_llm_config
from app.core.config import settings

print("🔧 Testing chat backend configuration...")
print(f"Chat service enabled: {settings.CHAT_SERVICE_ENABLED}")
print(f"Default provider: {settings.CHAT_DEFAULT_PROVIDER}")
print()

providers = ['openai', 'anthropic', 'custom']
configured_providers = []

for provider in providers:
    try:
        config = get_llm_config(provider)
        if config.api_key and config.api_key.strip():
            status = f"✅ {provider.upper()}: Configured"
            configured_providers.append(provider)
        else:
            status = f"❌ {provider.upper()}: No API key"
        print(f"{status}")
        print(f"   Model: {config.model}")
        print(f"   Base URL: {config.base_url}")
        print()
    except Exception as e:
        print(f"❌ {provider.upper()}: {str(e)}")
        print()

if configured_providers:
    print(f"🎉 Success! {len(configured_providers)} provider(s) configured: {', '.join(configured_providers)}")
    print("Chat service is ready to use!")
else:
    print("⚠️  Warning: No LLM providers are configured.")
    print("Please add at least one API key to your .env file:")
    print("  - OPENAI_API_KEY for OpenAI/GPT")
    print("  - ANTHROPIC_API_KEY for Anthropic/Claude")  
    print("  - CUSTOM_LLM_API_KEY + CUSTOM_LLM_BASE_URL for custom services")