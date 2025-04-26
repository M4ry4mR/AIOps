import os
import json
import requests
import unittest
from unittest.mock import patch, MagicMock

 
# Set environment variables directly in code
from azure_devops_agent import AzureDevOpsClient, GeminiAgent, DevOpsAgent


def test_url_parser():
    """Test URL parsing functionality"""
    client = AzureDevOpsClient("dummy_pat", "dummy_org")

    # Test URLs
    test_urls = [
        "https://azure.asax.ir/tfs/AsaProjects/CustomerDevelopment/_build/results?buildId=868491&view=logs&j=c6dc1ccb-b334-5d4e-8705-9a961a97b18b&t=0ada1057-2299-54a0-1d11-75e5dcfc5f1c",
        "https://dev.azure.com/myorg/myproject/_build/results?buildId=12345",
    ]

    print("\n=== Testing URL Parser ===")
    for url in test_urls:
        print(f"\nTesting URL: {url}")
        result = client.parse_azure_devops_url(url)
        print(f"Result: {json.dumps(result, indent=2)}")

    return client.parse_azure_devops_url(test_urls[0]) is not None


class TestDevOpsAgent(unittest.TestCase):
    @patch('azure_devops_agent.AzureDevOpsClient.get_build_logs')
    @patch('azure_devops_agent.GeminiAgent.analyze_logs')
    def test_process_request(self, mock_analyze_logs, mock_get_build_logs):
        """Test the process_request method with mocked dependencies"""
        # Setup mocks
        mock_get_build_logs.return_value = "Sample log content"
        mock_analyze_logs.return_value = "Analysis result"

        # Create agent
        agent = DevOpsAgent()

        # Patch the parse_azure_devops_url method
        with patch.object(agent.azure_client, 'parse_azure_devops_url') as mock_parse_url:
            mock_parse_url.return_value = {
                "type": "build",
                "base_url": "https://azure.asax.ir/tfs",
                "project": "CustomerDevelopment",
                "build_id": 868491,
                "job_id": "c6dc1ccb-b334-5d4e-8705-9a961a97b18b",
                "task_id": "0ada1057-2299-54a0-1d11-75e5dcfc5f1c"
            }

            # Test the process_request method
            result = agent.process_request(
                "https://azure.asax.ir/tfs/AsaProjects/CustomerDevelopment/_build/results?buildId=868491 What's the error?",
                "test_user_123"
            )

            # Assert the result
            self.assertEqual(result, "Analysis result")

            # Assert the mocks were called correctly
            mock_parse_url.assert_called_once()
            mock_get_build_logs.assert_called_once()
            mock_analyze_logs.assert_called_once()


def run_all_tests():
    print("Running all tests for Azure DevOps Error Analysis Agent")

    # Run functional tests
    url_parser_result = test_url_parser()
    print(f"\nURL Parser Test: {'PASSED' if url_parser_result else 'FAILED'}")

    # Run unit tests
    unittest.main(argv=['first-arg-is-ignored'], exit=False)


if __name__ == "__main__":
    run_all_tests()
