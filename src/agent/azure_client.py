import re
import base64
import logging
import requests
from typing import Dict

logger = logging.getLogger(__name__)

class AzureDevOpsClient:
    def __init__(self, pat: str, organization: str):
        self.pat = pat
        self.organization = organization
        self.headers = {"Authorization": f"Basic {self._encode_pat(pat)}"}
        logger.info(f"Initialized Azure DevOps client for organization: {organization}")

    def _encode_pat(self, pat: str) -> str:
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