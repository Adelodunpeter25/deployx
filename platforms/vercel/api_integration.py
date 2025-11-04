"""
Vercel API integration for direct deployment without CLI dependency.
"""
import os
import json
import requests
import tarfile
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from core.logging import get_logger

class VercelAPIIntegration:
    """Direct Vercel API integration for file upload and deployment."""
    
    def __init__(self, token: str):
        self.token = token
        self.api_base = "https://api.vercel.com"
        self.logger = get_logger(__name__)
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def create_project(self, project_name: str, framework: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """Create a new Vercel project via API."""
        try:
            payload = {
                "name": project_name,
                "framework": framework
            }
            
            response = requests.post(
                f"{self.api_base}/v9/projects",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                project_data = response.json()
                project_id = project_data.get('id')
                return True, f"Created project: {project_name}", project_id
            else:
                error_msg = response.json().get('error', {}).get('message', 'Unknown error')
                return False, f"Failed to create project: {error_msg}", None
                
        except Exception as e:
            return False, f"API error: {str(e)}", None
    
    def upload_files(self, project_path: str, output_dir: str) -> Tuple[bool, str, Optional[List[Dict]]]:
        """Upload project files to Vercel."""
        try:
            files_data = []
            build_path = Path(project_path) / output_dir
            
            if not build_path.exists():
                return False, f"Build directory not found: {build_path}", None
            
            # Collect all files
            for file_path in build_path.rglob('*'):
                if file_path.is_file():
                    relative_path = file_path.relative_to(build_path)
                    
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    
                    files_data.append({
                        "file": str(relative_path),
                        "data": file_content.hex()
                    })
            
            # Upload files
            payload = {"files": files_data}
            
            response = requests.post(
                f"{self.api_base}/v2/files",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                return True, "Files uploaded successfully", files_data
            else:
                error_msg = response.json().get('error', {}).get('message', 'Upload failed')
                return False, error_msg, None
                
        except Exception as e:
            return False, f"Upload error: {str(e)}", None
    
    def create_deployment(self, project_name: str, files: List[Dict]) -> Tuple[bool, str, Optional[str]]:
        """Create a deployment with uploaded files."""
        try:
            payload = {
                "name": project_name,
                "files": files,
                "projectSettings": {
                    "framework": None
                }
            }
            
            response = requests.post(
                f"{self.api_base}/v13/deployments",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code in [200, 201]:
                deployment_data = response.json()
                deployment_url = deployment_data.get('url')
                if deployment_url and not deployment_url.startswith('https://'):
                    deployment_url = f"https://{deployment_url}"
                
                return True, "Deployment created successfully", deployment_url
            else:
                error_msg = response.json().get('error', {}).get('message', 'Deployment failed')
                return False, error_msg, None
                
        except Exception as e:
            return False, f"Deployment error: {str(e)}", None
    
    def get_deployment_status(self, deployment_id: str) -> Tuple[bool, str, str]:
        """Get deployment status."""
        try:
            response = requests.get(
                f"{self.api_base}/v13/deployments/{deployment_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                deployment_data = response.json()
                status = deployment_data.get('readyState', 'UNKNOWN')
                url = deployment_data.get('url')
                
                return True, status, url
            else:
                return False, "Failed to get status", ""
                
        except Exception as e:
            return False, f"Status error: {str(e)}", ""
    
    def list_projects(self) -> Tuple[bool, List[Dict], str]:
        """List all projects."""
        try:
            response = requests.get(
                f"{self.api_base}/v9/projects",
                headers=self.headers
            )
            
            if response.status_code == 200:
                projects_data = response.json()
                projects = projects_data.get('projects', [])
                return True, projects, "Projects retrieved successfully"
            else:
                error_msg = response.json().get('error', {}).get('message', 'Failed to list projects')
                return False, [], error_msg
                
        except Exception as e:
            return False, [], f"API error: {str(e)}"
