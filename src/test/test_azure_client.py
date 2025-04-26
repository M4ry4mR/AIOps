import unittest
from unittest.mock import patch, MagicMock
import json
from src.agent.azure_client import AzureDevOpsClient

class TestAzureDevOpsClient(unittest.TestCase):
    def setUp(self):
        self.client = AzureDevOpsClient("dummy_pat", "dummy_org")
        
    def test_url_parser_tfs(self):
        """Test URL parsing for TFS URLs"""
        url = "https://azure.asax.ir/tfs/AsaProjects/CustomerDevelopment/_build/results?buildId=868491&view=logs&j=c6dc1ccb-b334-5d4e-8705-9a961a97b18b&t=0ada1057-2299-54a0-1d11-75e5dcfc5f1c"
        
        result = self.client.parse_azure_devops_url(url)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["build_id"], 868491)
        self.assertEqual(result["project"], "CustomerDevelopment")
        self.assertEqual(result["job_id"], "c6dc1ccb-b334-5d4e-8705-9a961a97b18b")
        self.assertEqual(result["task_id"], "0ada1057-2299-54a0-1d11-75e5dcfc5f1c")
        
    def test_url_parser_azure_devops(self):
        """Test URL parsing for Azure DevOps URLs"""
        url = "https://dev.azure.com/myorg/myproject/_build/results?buildId=12345"
        
        result = self.client.parse_azure_devops_url(url)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["build_id"], 12345)
        self.assertEqual(result["project"], "myproject")
        
    @patch('requests.get')
    def test_get_build_logs(self, mock_get):
        """Test retrieving build logs"""
        # Setup mock responses
        build_response = MagicMock()
        build_response.status_code = 200
        build_response.json.return_value = {"id": 12345, "status": "completed"}
        
        logs_list_response = MagicMock()
        logs_list_response.status_code = 200
        logs_list_response.json.return_value = {
            "value": [
                {"id": 1, "name": "Log 1"},
                {"id": 2, "name": "Log 2"}
            ]
        }
        
        log1_response = MagicMock()
        log1_response.status_code = 200
        log1_response.text = "Log 1 content"
        
        log2_response = MagicMock()
        log2_response.status_code = 200
        log2_response.text = "Log 2 content"
        
        # Configure mock to return different responses
        mock_get.side_effect = [
            build_response,
            logs_list_response,
            log1_response,
            log2_response
        ]
        
        # Test
        url_info = {
            "type": "build",
            "base_url": "https://dev.azure.com/myorg",
            "project": "myproject",
            "build_id": 12345
        }
        
        result = self.client.get_build_logs(url_info)
        
        # Verify
        self.assertIn("Log 1 content", result)
        self.assertIn("Log 2 content", result)
        self.assertEqual(mock_get.call_count, 4)

if __name__ == '__main__':
    unittest.main() 