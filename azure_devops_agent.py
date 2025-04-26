import os
import json
import requests
import re
import unittest
from unittest.mock import patch, MagicMock
import logging
from flask import Flask, request, jsonify, render_template_string
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
import httpx

 
 

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)


class AzureDevOpsClient:
    def __init__(self, pat: str, organization: str):
        self.pat = pat
        self.organization = organization
        self.headers = {"Authorization": f"Basic {self._encode_pat(pat)}"}
        logger.info(f"Initialized Azure DevOps client for organization: {organization}")

    def _encode_pat(self, pat: str) -> str:
        import base64
        return base64.b64encode(f":{pat}".encode()).decode()

    def parse_azure_devops_url(self, url: str) -> Dict:
        """Parse Azure DevOps/TFS URL to extract relevant information."""
        logger.info(f"Parsing URL: {url}")

        # Extract build ID
        build_id_match = re.search(r'buildId=(\d+)', url)
        if not build_id_match:
            logger.warning("Could not extract build ID from URL")
            return {}

        build_id = build_id_match.group(1)

        # Determine if it's a TFS or Azure DevOps URL
        if "tfs" in url.lower():
            base_url_match = re.search(r'(https?://[^/]+/tfs/[^/]+)', url)
            base_url = base_url_match.group(1) if base_url_match else None

            # Extract project name
            project_match = re.search(r'tfs/[^/]+/([^/]+)', url)
            project = project_match.group(1) if project_match else None
        else:
            base_url_match = re.search(r'(https?://dev\.azure\.com/[^/]+)', url)
            base_url = base_url_match.group(1) if base_url_match else None

            # Extract project name
            project_match = re.search(r'azure\.com/[^/]+/([^/]+)', url)
            project = project_match.group(1) if project_match else None

        # Extract job and task IDs if present
        job_id_match = re.search(r'j=([^&]+)', url)
        job_id = job_id_match.group(1) if job_id_match else None

        task_id_match = re.search(r't=([^&]+)', url)
        task_id = task_id_match.group(1) if task_id_match else None

        result = {
            "type": "build",
            "base_url": base_url,
            "project": project,
            "build_id": int(build_id),
        }

        if job_id:
            result["job_id"] = job_id
        if task_id:
            result["task_id"] = task_id

        logger.info(f"Parsed URL data: {result}")
        return result

    def get_build_logs(self, url_info: Dict) -> str:
        """Get build logs from Azure DevOps/TFS based on parsed URL info."""
        logger.info(f"Getting build logs for: {url_info}")

        if not url_info or "build_id" not in url_info:
            return "Could not parse build information from URL."

        try:
            build_id = url_info["build_id"]
            project = url_info["project"]
            base_url = url_info["base_url"]

            # Determine API endpoint based on whether it's TFS or Azure DevOps
            if "tfs" in base_url.lower():
                # For TFS, include the project in the path
                api_base = f"{base_url}/{project}/_apis"
            else:
                api_base = f"{base_url}/{project}/_apis"

            # First, get the build details
            build_url = f"{api_base}/build/builds/{build_id}?api-version=6.0"
            logger.info(f"Requesting build details from: {build_url}")

            response = requests.get(build_url, headers=self.headers)
            # Rest of the function remains the same...
            if response.status_code != 200:
                logger.error(f"Failed to get build details: {response.status_code} - {response.text}")
                return f"Failed to get build details: {response.status_code}"

            build_data = response.json()

            # Get logs URL
            logs_url = f"{api_base}/build/builds/{build_id}/logs?api-version=6.0"
            logger.info(f"Requesting log list from: {logs_url}")

            response = requests.get(logs_url, headers=self.headers)
            if response.status_code != 200:
                logger.error(f"Failed to get logs list: {response.status_code} - {response.text}")
                return f"Failed to get logs list: {response.status_code}"

            logs_data = response.json()

            # If job_id and task_id are specified, get those specific logs
            if "job_id" in url_info and "task_id" in url_info:
                # This is more complex and depends on the specific API structure
                # For simplicity, we'll get all logs for now
                pass

            # Get all logs
            all_logs = []
            for log in logs_data.get("value", []):
                log_id = log.get("id")
                if log_id:
                    log_url = f"{api_base}/build/builds/{build_id}/logs/{log_id}?api-version=6.0"
                    logger.info(f"Requesting log content from: {log_url}")

                    log_response = requests.get(log_url, headers=self.headers)
                    if log_response.status_code == 200:
                        all_logs.append(log_response.text)
                    else:
                        logger.warning(f"Failed to get log {log_id}: {log_response.status_code}")

            if not all_logs:
                return "No logs found for this build."

            return "\n\n===== LOG SECTION =====\n\n".join(all_logs)

        except Exception as e:
            logger.exception(f"Error retrieving build logs: {e}")
            return f"Error retrieving build logs: {str(e)}"


class AIAnalysisAgent:
    def __init__(self, api_key: str):
        self.api_key = api_key
        http_client = httpx.Client(verify=False)
        self.client = OpenAI(
            base_url="https://api.aimlapi.com/v1",
            api_key=api_key,
            http_client=http_client
        )
        logger.info("Initialized AI analysis agent")

    def analyze_logs(self, logs: str, query: str) -> str:
        """Analyze logs using OpenAI API."""
        logger.info(f"Analyzing logs with query: {query}")
        try:
            prompt = f"""You are an expert in Azure DevOps build and release pipelines. 
            I'll provide you with build or release logs, and I need your help to understand what went wrong.

            Please analyze these logs carefully and provide:
            1. A clear explanation of what the error is
            2. The most likely cause of the failure
            3. Specific steps to fix the issue

            Here's the specific question: {query}

            Here are the logs:
            {logs[:80000]}  # Trimming logs to fit context window
            """

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )

            logger.info("Successfully generated analysis")
            return response.choices[0].message.content
        except Exception as e:
            logger.exception(f"Error analyzing logs: {e}")
            return f"Error analyzing logs: {str(e)}"


class DevOpsAgent:
    def __init__(self):
        # Configuration
        self.azure_client = AzureDevOpsClient(
            os.environ.get("AZURE_DEVOPS_PAT"),
            os.environ.get("AZURE_DEVOPS_ORG")
        )
        self.ai_agent = AIAnalysisAgent(os.environ.get("AI_API_KEY"))
        logger.info("Initialized DevOpsAgent")

    def process_request(self, text: str, user_id: str) -> str:
        """Process a user request containing an Azure DevOps URL and question."""
        logger.info(f"Processing request from user {user_id}: {text}")

        # Extract URL from the message
        url_match = re.search(r'(https?://[^\s]+)', text)
        if not url_match:
            return "I couldn't find a valid Azure DevOps URL in your message. Please include the URL to the build or release you want me to analyze."

        url = url_match.group(1)
        logger.info(f"Extracted URL: {url}")

        # Extract question (everything after the URL)
        query = text[len(url):].strip()
        if not query:
            query = "What caused this build to fail and how can I fix it?"
        logger.info(f"Extracted query: {query}")

        # Parse the URL
        url_info = self.azure_client.parse_azure_devops_url(url)
        if not url_info:
            return "I couldn't parse that Azure DevOps URL. Please make sure it's a valid build or release URL."

        # Get logs
        logs = self.azure_client.get_build_logs(url_info)
        if not logs or logs.startswith("Failed") or logs.startswith("Error"):
            return f"I had trouble retrieving the logs: {logs}"

        # Analyze logs
        analysis = self.ai_agent.analyze_logs(logs, query)

        return analysis


devops_agent = DevOpsAgent()


# Web UI route
@app.route('/', methods=['GET', 'POST'])
def index():
    result = ""
    if request.method == 'POST':
        url = request.form.get('url', '')
        query = request.form.get('query', 'What caused this build to fail and how can I fix it?')
        text = f"{url} {query}"
        result = devops_agent.process_request(text, "web_user")

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Azure DevOps Error Analyzer</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
            .container { max-width: 800px; margin: 0 auto; }
            h1 { color: #0078d7; }
            form { margin: 20px 0; padding: 20px; background: #f9f9f9; border-radius: 8px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input[type="text"], textarea { width: 100%; padding: 8px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 4px; }
            textarea { height: 100px; }
            input[type="submit"] { background: #0078d7; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; }
            input[type="submit"]:hover { background: #005a9e; }
            .result { margin-top: 20px; padding: 20px; background: #f0f7ff; border-radius: 8px; white-space: pre-wrap; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Azure DevOps Error Analyzer</h1>
            <p>Enter an Azure DevOps build URL and your question about the build errors.</p>

            <form method="post">
                <div>
                    <label for="url">Azure DevOps URL:</label>
                    <input type="text" id="url" name="url" placeholder="https://azure.asax.ir/tfs/AsaProjects/..." required>
                </div>
                <div>
                    <label for="query">Your Question:</label>
                    <textarea id="query" name="query" placeholder="What caused this build to fail and how can I fix it?"></textarea>
                </div>
                <input type="submit" value="Analyze">
            </form>

            {% if result %}
            <div class="result">
                <h2>Analysis Result:</h2>
                {{ result }}
            </div>
            {% endif %}
        </div>
    </body>
    </html>
    """

    return render_template_string(html, result=result)


@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    data = request.json
    if not data or 'text' not in data:
        return jsonify({"error": "Missing required parameter: text"}), 400

    text = data['text']
    user_id = data.get('user_id', 'api_user')

    result = devops_agent.process_request(text, user_id)
    return jsonify({"result": result})


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=7000)