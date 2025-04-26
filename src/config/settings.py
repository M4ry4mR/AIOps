import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Azure DevOps settings
AZURE_DEVOPS_PAT = os.environ.get("AZURE_DEVOPS_PAT")
AZURE_DEVOPS_ORG = os.environ.get("AZURE_DEVOPS_ORG")

# AI settings
AI_API_KEY = os.environ.get("AI_API_KEY")
AI_API_BASE_URL = os.environ.get("AI_API_BASE_URL", "https://api.aimlapi.com/v1")
AI_MODEL = os.environ.get("AI_MODEL", "gpt-4o")

# OpenRouter settings
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# Gemini settings
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")

# Model provider options
AI_PROVIDERS = {
    "openai": "OpenAI",
    "openrouter": "OpenRouter",
    "gemini": "Gemini"
}

# Default AI provider
DEFAULT_AI_PROVIDER = os.environ.get("DEFAULT_AI_PROVIDER", "openai")

# Zoho Cliq settings
ZOHO_CLIQ_BOT_NAME = os.environ.get("ZOHO_CLIQ_BOT_NAME")
ZOHO_CLIQ_WEBHOOK_TOKEN = os.environ.get("ZOHO_CLIQ_WEBHOOK_TOKEN") 