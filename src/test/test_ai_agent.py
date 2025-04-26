import unittest
from unittest.mock import patch, MagicMock
from src.agent.ai_agent import AIAnalysisAgent

class TestAIAnalysisAgent(unittest.TestCase):
    def setUp(self):
        # Use patch to avoid actual initialization of providers
        with patch('src.agent.ai_providers.OpenAIProvider') as mock_provider:
            mock_instance = MagicMock()
            mock_provider.return_value = mock_instance
            self.agent = AIAnalysisAgent(api_key="test_key", provider="openai")
            self.mock_provider = mock_instance
    
    @patch('src.agent.ai_providers.get_ai_provider')
    def test_analyze_logs(self, mock_get_provider):
        """Test the analyze_logs method with mocked provider"""
        # Setup mock
        mock_provider = MagicMock()
        mock_provider.analyze_logs.return_value = "Analysis of the logs"
        mock_get_provider.return_value = mock_provider
        
        # Create new agent with the mocked provider
        agent = AIAnalysisAgent(api_key="test_key", provider="openai")
        
        # Test
        logs = "Sample log content"
        query = "What went wrong?"
        
        result = agent.analyze_logs(logs, query)
        
        # Verify
        self.assertEqual(result, "Analysis of the logs")
        mock_provider.analyze_logs.assert_called_once_with(logs, query)
    
    @patch('src.agent.ai_providers.get_ai_provider')
    def test_change_provider(self, mock_get_provider):
        """Test changing providers"""
        # Setup mocks
        mock_provider1 = MagicMock()
        mock_provider2 = MagicMock()
        
        # First call returns provider1, second call returns provider2
        mock_get_provider.side_effect = [mock_provider1, mock_provider2]
        
        # Create agent with initial provider
        agent = AIAnalysisAgent(api_key="test_key", provider="openai")
        
        # Change provider
        agent.change_provider("gemini", "gemini-1.5-pro")
        
        # Verify
        self.assertEqual(agent.provider_name, "gemini")
        self.assertEqual(agent.model, "gemini-1.5-pro")
        mock_get_provider.assert_called_with("gemini", "gemini-1.5-pro")
    
    @patch('src.agent.ai_providers.get_ai_provider')
    def test_analyze_logs_error(self, mock_get_provider):
        """Test error handling in analyze_logs"""
        # Setup mock to raise an exception
        mock_provider = MagicMock()
        mock_provider.analyze_logs.side_effect = Exception("API error")
        mock_get_provider.return_value = mock_provider
        
        # Create agent with the mocked provider
        agent = AIAnalysisAgent(api_key="test_key", provider="openai")
        
        # Test
        logs = "Sample log content"
        query = "What went wrong?"
        
        result = agent.analyze_logs(logs, query)
        
        # Verify error is handled gracefully
        self.assertIn("Error analyzing logs", result)

if __name__ == '__main__':
    unittest.main() 