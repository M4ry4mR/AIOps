import re
import logging
from typing import Optional
from src.agent.azure_client import AzureDevOpsClient
from src.agent.ai_agent import AIAnalysisAgent
from src.config.settings import (
    AZURE_DEVOPS_PAT, AZURE_DEVOPS_ORG, 
    AI_API_KEY, DEFAULT_AI_PROVIDER
)

logger = logging.getLogger(__name__)

class DevOpsAgent:
    def __init__(self):
        # Configuration
        logger.info("Initializing Azure DevOps client")
        self.azure_client = AzureDevOpsClient(
            AZURE_DEVOPS_PAT,
            AZURE_DEVOPS_ORG
        )
        
        logger.info("Initializing AI Analysis agent")
        self.ai_agent = AIAnalysisAgent(
            api_key=AI_API_KEY,
            provider=DEFAULT_AI_PROVIDER
        )
        logger.info("DevOpsAgent initialization complete")

    def process_request(self, text: str, user_id: str, provider: Optional[str] = None, model: Optional[str] = None) -> str:
        """Process a user request containing an Azure DevOps URL and question."""
        logger.info(f"Processing request from user {user_id}: {text}")
        
        # Add more detailed debugging
        logger.info(f"Text being processed for URL extraction: '{text}'")
        
        # Change AI provider if specified
        if provider and provider != self.ai_agent.provider_name:
            logger.info(f"Changing AI provider from {self.ai_agent.provider_name} to {provider} with model {model}")
            self.ai_agent.change_provider(provider, model)
            logger.info(f"Changed AI provider to {provider} with model {model}")

        # Extract URL from the message - modified to handle URLs with @ prefix
        # Try multiple patterns to maximize chances of finding the URL
        url_patterns = [
            r'(?:^|\s)@?(https?://[^\s]+)',  # Standard URL with optional @ prefix
            r'(?:^|\s)(azure\.asax\.ir[^\s]+)',  # Domain without protocol
            r'(?:^|\s)(tfs/[^\s]+)',  # Partial TFS path
            r'buildId=(\d+)'  # Just the build ID
        ]
        
        url_match = None
        for pattern in url_patterns:
            match = re.search(pattern, text)
            if match:
                url_match = match
                logger.info(f"URL match found with pattern '{pattern}': {match.group(0)}")
                break
                
        # More debugging for regex matching
        if url_match:
            logger.info(f"URL match found: '{url_match.group(0)}' -> '{url_match.group(1)}'")
        else:
            logger.info(f"No URL match found in text: '{text}'")
            
        if not url_match:
            logger.warning("No valid Azure DevOps URL found in the message")
            return "I couldn't find a valid Azure DevOps URL in your message. Please include the URL to the build or release you want me to analyze."

        # Extract the URL based on what was matched
        url = url_match.group(1)
        
        # If we matched a partial URL, try to reconstruct it
        if not url.startswith('http'):
            if url.startswith('azure.asax.ir'):
                url = 'https://' + url
            elif url.startswith('tfs/'):
                url = 'https://azure.asax.ir/' + url
            elif url.isdigit():  # We matched just a build ID
                url = f'https://azure.asax.ir/tfs/AsaProjects/Financial/_build/results?buildId={url}'
                
        logger.info(f"Extracted URL: {url}")

        # Extract question (everything after the URL)
        query = text[len(url):].strip()
        if not query:
            query = "What caused this build to fail and how can I fix it?"
        logger.info(f"Extracted query: {query}")

        # Parse the URL
        logger.info("Parsing Azure DevOps URL")
        url_info = self.azure_client.parse_azure_devops_url(url)
        if not url_info:
            logger.warning("Failed to parse Azure DevOps URL")
            return "I couldn't parse that Azure DevOps URL. Please make sure it's a valid build or release URL."

        # Get logs
        logger.info(f"Retrieving logs for build ID: {url_info.get('build_id', 'unknown')}")
        logs = self.azure_client.get_build_logs(url_info)
        if not logs or logs.startswith("Failed") or logs.startswith("Error"):
            logger.error(f"Failed to retrieve logs: {logs}")
            return f"I had trouble retrieving the logs: {logs}"

        logger.info(f"Successfully retrieved logs ({len(logs)} characters)")
        
        # Analyze logs
        logger.info(f"Starting log analysis with provider {self.ai_agent.provider_name}")
        analysis = self.ai_agent.analyze_logs(logs, query)
        logger.info("Analysis complete")

        return analysis 