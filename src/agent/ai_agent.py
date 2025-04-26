import logging
from typing import Optional
from src.agent.ai_providers import get_ai_provider
from src.config.settings import DEFAULT_AI_PROVIDER

logger = logging.getLogger(__name__)

class AIAnalysisAgent:
    def __init__(self, api_key: str = None, provider: str = None, model: str = None):
        """Initialize AI analysis agent with the specified provider."""
        self.provider_name = provider or DEFAULT_AI_PROVIDER
        self.model = model
        self.api_key = api_key
        
        # Initialize the appropriate provider
        self.provider = get_ai_provider(self.provider_name, self.model)
        logger.info(f"Initialized AI analysis agent with provider: {self.provider_name}")

    def analyze_logs(self, logs: str, query: str) -> str:
        """Analyze logs using the selected AI provider."""
        logger.info(f"Analyzing logs with provider {self.provider_name}")
        try:
            return self.provider.analyze_logs(logs, query)
        except Exception as e:
            logger.exception(f"Error in AI analysis: {e}")
            return f"Error analyzing logs: {str(e)}"
            
    def change_provider(self, provider: str, model: Optional[str] = None) -> None:
        """Change the AI provider dynamically."""
        logger.info(f"Changing AI provider from {self.provider_name} to {provider}")
        self.provider_name = provider
        self.model = model
        self.provider = get_ai_provider(provider, model) 