"""
Render API client for service management.

Handles all Render API interactions including service creation,
management, and deployment operations.
"""
import requests
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class RenderService:
    """Render service information."""
    id: str
    name: str
    type: str
    repo: str
    branch: str
    url: Optional[str] = None

class RenderAPIClient:
    """Client for Render API operations."""
    
    BASE_URL = "https://api.render.com/v1"
    
    def __init__(self, api_key: str):
        """
        Initialize Render API client.
        
        Args:
            api_key: Render API key for authentication
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def create_service(self, name: str, service_type: str, repo_url: str, 
                      branch: str = "main", build_command: Optional[str] = None,
                      publish_path: Optional[str] = None) -> Tuple[bool, RenderService, str]:
        """
        Create a new Render service.
        
        Args:
            name: Service name
            service_type: Type of service (web_service, static_site)
            repo_url: Git repository URL
            branch: Git branch to deploy
            build_command: Build command for the service
            publish_path: Directory to serve static files from
            
        Returns:
            Tuple of (success, service_info, error_message)
        """
        payload = {
            "name": name,
            "type": service_type,
            "repo": repo_url,
            "branch": branch
        }
        
        if service_type == "static_site":
            payload["staticSite"] = {
                "buildCommand": build_command or "",
                "publishPath": publish_path or "."
            }
        elif service_type == "web_service":
            payload["webService"] = {
                "buildCommand": build_command or "",
                "startCommand": "npm start"  # Default start command
            }
        
        try:
            response = requests.post(
                f"{self.BASE_URL}/services",
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 201:
                data = response.json()
                service = RenderService(
                    id=data["id"],
                    name=data["name"],
                    type=data["type"],
                    repo=data["repo"],
                    branch=data["branch"],
                    url=data.get("serviceDetails", {}).get("url")
                )
                return True, service, ""
            else:
                error_msg = response.json().get("message", f"HTTP {response.status_code}")
                return False, None, f"Failed to create service: {error_msg}"
                
        except requests.exceptions.RequestException as e:
            return False, None, f"API request failed: {str(e)}"
    
    def get_service(self, service_id: str) -> Tuple[bool, Optional[RenderService], str]:
        """
        Get service information by ID.
        
        Args:
            service_id: Render service ID
            
        Returns:
            Tuple of (success, service_info, error_message)
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/services/{service_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                service = RenderService(
                    id=data["id"],
                    name=data["name"],
                    type=data["type"],
                    repo=data["repo"],
                    branch=data["branch"],
                    url=data.get("serviceDetails", {}).get("url")
                )
                return True, service, ""
            elif response.status_code == 404:
                return False, None, "Service not found"
            else:
                error_msg = response.json().get("message", f"HTTP {response.status_code}")
                return False, None, f"Failed to get service: {error_msg}"
                
        except requests.exceptions.RequestException as e:
            return False, None, f"API request failed: {str(e)}"
    
    def list_services(self) -> Tuple[bool, list, str]:
        """
        List all services for the authenticated user.
        
        Returns:
            Tuple of (success, services_list, error_message)
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/services",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                services = []
                for item in response.json():
                    service = RenderService(
                        id=item["id"],
                        name=item["name"],
                        type=item["type"],
                        repo=item["repo"],
                        branch=item["branch"],
                        url=item.get("serviceDetails", {}).get("url")
                    )
                    services.append(service)
                return True, services, ""
            else:
                error_msg = response.json().get("message", f"HTTP {response.status_code}")
                return False, [], f"Failed to list services: {error_msg}"
                
        except requests.exceptions.RequestException as e:
            return False, [], f"API request failed: {str(e)}"
