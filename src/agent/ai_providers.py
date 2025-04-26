import logging
import httpx
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from openai import OpenAI
from src.config.settings import (
    AI_API_KEY, AI_API_BASE_URL, AI_MODEL,
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL,
    GEMINI_API_KEY, GEMINI_MODEL
)

logger = logging.getLogger(__name__)

class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def analyze_logs(self, logs: str, query: str) -> str:
        """Analyze logs using AI and return the analysis."""
        pass

class OpenAIProvider(AIProvider):
    """OpenAI implementation."""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        """Initialize OpenAI client."""
        self.api_key = api_key or AI_API_KEY
        self.base_url = base_url or AI_API_BASE_URL
        self.model = model or AI_MODEL
        
        http_client = httpx.Client(verify=False)
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            http_client=http_client
        )
        logger.info(f"Initialized OpenAI provider with model: {self.model}")
    
    def analyze_logs(self, logs: str, query: str) -> str:
        """Analyze logs using OpenAI API."""
        logger.info(f"Analyzing logs with OpenAI model {self.model}")
        try:
            prompt = self._create_prompt(logs, query)
            
            # Log progress
            logger.info("Sending request to OpenAI API")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            logger.info("Successfully generated analysis with OpenAI")
            return response.choices[0].message.content
        except Exception as e:
            logger.exception(f"Error analyzing logs with OpenAI: {e}")
            return f"Error analyzing logs with OpenAI: {str(e)}"
    
    def _create_prompt(self, logs: str, query: str) -> str:
        """Create a prompt for the OpenAI model."""
        return f"""You are an expert in Azure DevOps build and release pipelines. 
        I'll provide you with build or release logs, and I need your help to understand what went wrong.

        Please analyze these logs carefully and provide:
        1. A clear explanation of what the error is
        2. The most likely cause of the failure
        3. Specific steps to fix the issue

        Here's the specific question: {query}

        Here are the logs:
        {logs[:80000]}  # Trimming logs to fit context window
        """

class OpenRouterProvider(AIProvider):
    """OpenRouter implementation."""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        """Initialize OpenRouter client."""
        self.api_key = api_key or OPENROUTER_API_KEY
        self.base_url = base_url or OPENROUTER_BASE_URL
        self.model = model or "openai/gpt-4-turbo"  # Default model
        
        http_client = httpx.Client(verify=False)
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            http_client=http_client,
            default_headers={
                "HTTP-Referer": "https://azuredevopsagent.app",
                "X-Title": "Azure DevOps Log Analyzer"
            }
        )
        logger.info(f"Initialized OpenRouter provider with model: {self.model}")
    
    def analyze_logs(self, logs: str, query: str) -> str:
        """Analyze logs using OpenRouter API."""
        logger.info(f"Analyzing logs with OpenRouter model {self.model}")
        try:
            prompt = self._create_prompt(logs, query)
            
            # Log progress
            logger.info("Sending request to OpenRouter API")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            logger.info("Successfully generated analysis with OpenRouter")
            return response.choices[0].message.content
        except Exception as e:
            logger.exception(f"Error analyzing logs with OpenRouter: {e}")
            return f"Error analyzing logs with OpenRouter: {str(e)}"
    
    def _create_prompt(self, logs: str, query: str) -> str:
        """Create a prompt for the OpenRouter model."""
        return f"""You are an expert in Azure DevOps build and release pipelines. 
        I'll provide you with build or release logs, and I need your help to understand what went wrong.

        Please analyze these logs carefully and provide:
        1. A clear explanation of what the error is
        2. The most likely cause of the failure
        3. Specific steps to fix the issue

        Here's the specific question: {query}

        Here are the logs:
        {logs[:80000]}  # Trimming logs to fit context window
        """

class GeminiProvider(AIProvider):
    """Google Gemini AI implementation."""
    
    def __init__(self, api_key: str = None, model: str = None):
        """Initialize Gemini client."""
        self.api_key = api_key or GEMINI_API_KEY
        self.model = model or GEMINI_MODEL
        
        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        
        # Initialize the model
        self.gemini_model = genai.GenerativeModel(self.model)
        logger.info(f"Initialized Gemini provider with model: {self.model}")
    
    def analyze_logs(self, logs: str, query: str) -> str:
        """Analyze logs using Gemini API."""
        logger.info(f"Analyzing logs with Gemini model {self.model}")
        try:
            prompt = self._create_prompt(logs, query)
            
            # Log progress
            logger.info("Sending request to Gemini API")
            
            response = self.gemini_model.generate_content(prompt)
            
            logger.info("Successfully generated analysis with Gemini")
            return response.text
        except Exception as e:
            logger.exception(f"Error analyzing logs with Gemini: {e}")
            return f"Error analyzing logs with Gemini: {str(e)}"
    
    def _create_prompt(self, logs: str, query: str) -> str:
        """Create a prompt for the Gemini model."""
        return f"""You are an expert in Azure DevOps build and release pipelines. 
        I'll provide you with build or release logs, and I need your help to understand what went wrong.

        Please analyze these logs carefully and provide:
        1. A clear explanation of what the error is
        2. The most likely cause of the failure
        3. Specific steps to fix the issue

        Here's the specific question: {query}

        Here are the logs:
        {logs[:50000]}  # Gemini may have a smaller context window
        """

def get_ai_provider(provider_name: str = "openai", model: Optional[str] = None) -> AIProvider:
    """Factory function to get the appropriate AI provider."""
    logger.info(f"Creating AI provider for: {provider_name}")
    
    if provider_name == "openai":
        return OpenAIProvider(model=model)
    elif provider_name == "openrouter":
        return OpenRouterProvider(model=model)
    elif provider_name == "gemini":
        return GeminiProvider(model=model)
    else:
        logger.warning(f"Unknown provider '{provider_name}', falling back to OpenAI")
        return OpenAIProvider(model=model) 