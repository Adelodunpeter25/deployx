"""
Netlify API integration for direct deployment without CLI dependency.
"""
import os
import requests
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from core.logging import get_logger

class NetlifyAPIIntegration:
    """Direct Netlify API integration for site creation and deployment."""
    
    def __init__(self, token: str):
        self.token = token
        self.api_base = "https://api.netlify.com/api/v1"
        self.logger = get_logger(__name__)
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def validate_token(self) -> Tuple[bool, str, Optional[Dict]]:
        """Validate Netlify token and get user info."""
        try:
            response = requests.get(f"{self.api_base}/user", headers=self.headers)
            
            if response.status_code == 200:
                user_data = response.json()
                email = user_data.get('email', 'Unknown')
                return True, f"Authenticated as {email}", user_data
            elif response.status_code == 401:
                return False, "Invalid token", None
            else:
                return False, f"API error: {response.status_code}", None
                
        except Exception as e:
            return False, f"Connection error: {str(e)}", None
    
    def create_site(self, site_name: str, custom_domain: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """Create a new Netlify site."""
        try:
            payload = {
                "name": site_name
            }
            
            if custom_domain:
                payload["custom_domain"] = custom_domain
            
            response = requests.post(
                f"{self.api_base}/sites",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 201:
                site_data = response.json()
                site_id = site_data.get('id')
                site_url = site_data.get('url')
                return True, f"Created site: {site_name}", site_id
            else:
                error_msg = response.json().get('message', 'Unknown error')
                return False, f"Failed to create site: {error_msg}", None
                
        except Exception as e:
            return False, f"API error: {str(e)}", None
    
    def deploy_site(self, site_id: str, project_path: str, build_dir: str) -> Tuple[bool, str, Optional[str]]:
        """Deploy site by uploading files as zip."""
        try:
            build_path = Path(project_path) / build_dir
            
            if not build_path.exists():
                return False, f"Build directory not found: {build_path}", None
            
            # Create zip file of build directory
            zip_path = self._create_deployment_zip(build_path)
            
            try:
                # Upload zip file
                with open(zip_path, 'rb') as zip_file:
                    files = {'file': zip_file}
                    headers = {"Authorization": f"Bearer {self.token}"}
                    
                    response = requests.post(
                        f"{self.api_base}/sites/{site_id}/deploys",
                        headers=headers,
                        files=files
                    )
                
                if response.status_code == 200:
                    deploy_data = response.json()
                    deploy_url = deploy_data.get('url')
                    return True, "Deployment successful", deploy_url
                else:
                    error_msg = response.json().get('message', 'Deployment failed')
                    return False, error_msg, None
                    
            finally:
                # Clean up zip file
                os.unlink(zip_path)
                
        except Exception as e:
            return False, f"Deployment error: {str(e)}", None
    
    def get_site_info(self, site_id: str) -> Tuple[bool, Optional[Dict], str]:
        """Get site information."""
        try:
            response = requests.get(
                f"{self.api_base}/sites/{site_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                site_data = response.json()
                return True, site_data, "Site info retrieved"
            elif response.status_code == 404:
                return False, None, "Site not found"
            else:
                return False, None, f"API error: {response.status_code}"
                
        except Exception as e:
            return False, None, f"Query error: {str(e)}"
    
    def list_sites(self) -> Tuple[bool, List[Dict], str]:
        """List all user sites."""
        try:
            response = requests.get(f"{self.api_base}/sites", headers=self.headers)
            
            if response.status_code == 200:
                sites = response.json()
                return True, sites, f"Found {len(sites)} sites"
            else:
                return False, [], f"API error: {response.status_code}"
                
        except Exception as e:
            return False, [], f"Query error: {str(e)}"
    
    def get_deployment_status(self, site_id: str) -> Tuple[bool, str, Optional[str]]:
        """Get latest deployment status for a site."""
        try:
            response = requests.get(
                f"{self.api_base}/sites/{site_id}/deploys",
                headers=self.headers,
                params={"per_page": 1}
            )
            
            if response.status_code == 200:
                deploys = response.json()
                if deploys:
                    latest_deploy = deploys[0]
                    status = latest_deploy.get('state', 'unknown')
                    url = latest_deploy.get('url')
                    return True, status, url
                else:
                    return True, "no_deploys", None
            else:
                return False, "error", None
                
        except Exception as e:
            return False, "error", None
    
    def _create_deployment_zip(self, build_path: Path) -> str:
        """Create a zip file of the build directory."""
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
            zip_path = tmp_file.name
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in build_path.rglob('*'):
                if file_path.is_file():
                    # Get relative path from build directory
                    relative_path = file_path.relative_to(build_path)
                    zip_file.write(file_path, relative_path)
        
        return zip_path
