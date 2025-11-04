"""
GitHub API integration for direct operations.
"""
import requests
from typing import Dict, Optional, Tuple
from core.logging import get_logger

class GitHubAPIIntegration:
    """Direct GitHub API integration."""
    
    def __init__(self, token: str):
        self.token = token
        self.api_base = "https://api.github.com"
        self.logger = get_logger(__name__)
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def validate_token(self) -> Tuple[bool, str, Optional[Dict]]:
        """Validate GitHub token."""
        try:
            response = requests.get(f"{self.api_base}/user", headers=self.headers)
            if response.status_code == 200:
                user_data = response.json()
                return True, f"Authenticated as {user_data.get('login')}", user_data
            else:
                return False, "Invalid token", None
        except Exception as e:
            return False, f"Connection error: {str(e)}", None
