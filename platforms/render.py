"""
Render deployment platform implementation
"""

import os
import requests
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from .base import BasePlatform, DeploymentResult, DeploymentStatus
from utils.errors import AuthenticationError

class RenderPlatform(BasePlatform):
    """Render deployment platform"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_base = "https://api.render.com/v1"
        self.project_path = config.get('project_path', '.')
        self.token = self._get_token()
        self.service_id = config.get("render", {}).get("service_id")
        
    def _get_token(self) -> str:
        """Get Render token from file or environment"""
        token_file = Path('.deployx_render_token')
        
        if token_file.exists():
            try:
                with open(token_file, 'r') as f:
                    return f.read().strip()
            except Exception:
                pass
            
        token = os.getenv("RENDER_TOKEN")
        if not token:
            raise AuthenticationError("Render token not found. Run 'deployx init' to configure.")
        return token
    
    def validate_credentials(self) -> Tuple[bool, str]:
        """Validate Render credentials"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.api_base}/owners", headers=headers)
            
            if response.status_code == 200:
                owners = response.json()
                if owners:
                    return True, f"Authenticated as {owners[0].get('name', 'user')}"
                else:
                    return True, "Authenticated successfully"
            else:
                return False, f"Invalid token (HTTP {response.status_code})"
                
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def prepare_deployment(self, project_path: str, build_command: Optional[str], output_dir: str) -> Tuple[bool, str]:
        """Prepare deployment files"""
        try:
            # Run build if configured
            if build_command:
                result = subprocess.run(
                    build_command.split(),
                    cwd=project_path,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    return False, f"Build failed: {result.stderr}"
            
            return True, "Deployment prepared successfully"
            
        except Exception as e:
            return False, f"Preparation failed: {str(e)}"
    
    def execute_deployment(self, project_path: str, output_dir: str) -> DeploymentResult:
        """Execute deployment to Render"""
        try:
            # Render deployments are typically triggered via git push
            # or manual deploy via API
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            if self.service_id:
                # Trigger manual deploy for existing service
                response = requests.post(
                    f"{self.api_base}/services/{self.service_id}/deploys",
                    headers=headers
                )
                
                if response.status_code == 201:
                    deploy_data = response.json()
                    return DeploymentResult(
                        success=True,
                        message="Deployment triggered successfully",
                        deployment_id=deploy_data.get("id")
                    )
                else:
                    return DeploymentResult(
                        success=False,
                        message=f"Deployment failed (HTTP {response.status_code})"
                    )
            else:
                return DeploymentResult(
                    success=False,
                    message="No service ID configured. Create service first."
                )
                
        except Exception as e:
            return DeploymentResult(success=False, message=f"Deployment failed: {str(e)}")
    
    def get_status(self, deployment_id: Optional[str] = None) -> DeploymentStatus:
        """Get deployment status"""
        try:
            if not self.service_id:
                return DeploymentStatus(status="unknown", message="No service ID configured")
                
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Get service details
            response = requests.get(
                f"{self.api_base}/services/{self.service_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                service = response.json()
                
                # Get latest deploy
                deploys_response = requests.get(
                    f"{self.api_base}/services/{self.service_id}/deploys",
                    headers=headers,
                    params={"limit": 1}
                )
                
                if deploys_response.status_code == 200:
                    deploys = deploys_response.json()
                    if deploys:
                        deploy = deploys[0]
                        status = deploy.get("status", "unknown").lower()
                        
                        status_map = {
                            "live": "ready",
                            "build_in_progress": "building",
                            "update_in_progress": "building",
                            "build_failed": "error",
                            "update_failed": "error",
                            "canceled": "error"
                        }
                        
                        return DeploymentStatus(
                            status=status_map.get(status, "unknown"),
                            url=service.get("serviceDetails", {}).get("url"),
                            last_updated=deploy.get("createdAt"),
                            message=f"Render service {status}"
                        )
            
            return DeploymentStatus(status="unknown", message="Service not found")
            
        except Exception as e:
            return DeploymentStatus(status="error", message=f"Status check failed: {str(e)}")
    
    def get_url(self) -> Optional[str]:
        """Get deployment URL"""
        status = self.get_status()
        return status.url