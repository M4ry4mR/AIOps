import unittest
from unittest.mock import patch, MagicMock
from src.agent.devops_agent import DevOpsAgent

class TestDevOpsAgent(unittest.TestCase):
    @patch('src.agent.ai_providers.get_ai_provider')
    def setUp(self, mock_get_provider):
        # Setup mock provider
        self.mock_provider = MagicMock()
        mock_get_provider.return_value = self.mock_provider
        
        self.agent = DevOpsAgent()
    
    @patch('src.agent.azure_client.AzureDevOpsClient.get_build_logs')
    def test_process_request(self, mock_get_build_logs):
        """Test the process_request method with mocked dependencies"""
        # Setup mocks
        mock_get_build_logs.return_value = "Sample log content"
        self.mock_provider.analyze_logs.return_value = "Analysis result"
        
        # Patch the parse_azure_devops_url method
        with patch.object(self.agent.azure_client, 'parse_azure_devops_url') as mock_parse_url:
            mock_parse_url.return_value = {
                "type": "build",
                "base_url": "https://azure.asax.ir/tfs",
                "project": "CustomerDevelopment",
                "build_id": 868491,
                "job_id": "c6dc1ccb-b334-5d4e-8705-9a961a97b18b",
                "task_id": "0ada1057-2299-54a0-1d11-75e5dcfc5f1c"
            }
            
            # Test with URL and query
            result = self.agent.process_request(
                "https://azure.asax.ir/tfs/AsaProjects/CustomerDevelopment/_build/results?buildId=868491 What's the error?",
                "test_user_123"
            )
            
            # Assert the result
            self.assertEqual(result, "Analysis result")
            
            # Assert the mocks were called correctly
            mock_parse_url.assert_called_once()
            mock_get_build_logs.assert_called_once()
            self.mock_provider.analyze_logs.assert_called_once()
    
    def test_process_request_no_url(self):
        """Test process_request with no URL provided"""
        result = self.agent.process_request("There is no URL here", "test_user")
        self.assertIn("I couldn't find a valid Azure DevOps URL", result)
    
    @patch('src.agent.azure_client.AzureDevOpsClient.parse_azure_devops_url')
    def test_process_request_invalid_url(self, mock_parse_url):
        """Test process_request with invalid URL"""
        mock_parse_url.return_value = {}
        
        result = self.agent.process_request("https://example.com invalid URL", "test_user")
        self.assertIn("I couldn't parse that Azure DevOps URL", result)
    
    @patch('src.agent.azure_client.AzureDevOpsClient.get_build_logs')
    @patch('src.agent.ai_agent.AIAnalysisAgent.change_provider')
    def test_process_request_with_provider(self, mock_change_provider, mock_get_build_logs):
        """Test process_request with provider selection"""
        # Setup mocks
        mock_get_build_logs.return_value = "Sample log content"
        self.mock_provider.analyze_logs.return_value = "Analysis with custom provider"
        
        # Patch the parse_azure_devops_url method
        with patch.object(self.agent.azure_client, 'parse_azure_devops_url') as mock_parse_url:
            mock_parse_url.return_value = {
                "type": "build",
                "base_url": "https://dev.azure.com/org",
                "project": "project",
                "build_id": 123
            }
            
            # Test with URL, query, and provider selection
            result = self.agent.process_request(
                "https://dev.azure.com/org/project/_build/results?buildId=123 What's wrong?",
                "test_user",
                provider="gemini",
                model="gemini-1.5-pro"
            )
            
            # Assert the change_provider was called
            mock_change_provider.assert_called_once_with("gemini", "gemini-1.5-pro")
            
            # Assert the result
            self.assertEqual(result, "Analysis with custom provider")

if __name__ == '__main__':
    unittest.main() 