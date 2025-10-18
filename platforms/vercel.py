"""
Vercel deployment platform implementation
"""

import os
import json
import requests
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from .base import BasePlatform, DeploymentResult, DeploymentStatus
from utils.errors import AuthenticationError

class VercelPlatform(BasePlatform):
    """Vercel deployment platform"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_base = "https://api.vercel.com"
        self.project_path = config.get('project_path', '.')
        self.token = self._get_token()
        
    def _get_token(self) -> str:
        """Get Vercel token from file or environment"""
        token_file = Path('.deployx_vercel_token')
        
        if token_file.exists():
            try:
                with open(token_file, 'r') as f:
                    return f.read().strip()
            except Exception:
                pass
            
        token = os.getenv("VERCEL_TOKEN")
        if not token:
            raise AuthenticationError("Vercel token not found. Run 'deployx init' to configure.")
        return token
    
    def validate_credentials(self) -> Tuple[bool, str]:
        """Validate Vercel credentials"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.api_base}/v2/user", headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                return True, f"Authenticated as {user_data.get('username', 'user')}"
            else:
                return False, f"Invalid token (HTTP {response.status_code})"
                
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def prepare_deployment(self, project_path: str, build_command: Optional[str], output_dir: str) -> Tuple[bool, str]:
        """Prepare deployment files"""
        try:
            # Check if vercel.json exists, create if needed
            vercel_config = Path(self.project_path) / "vercel.json"
            if not vercel_config.exists():
                config = {
                    "version": 2,
                    "name": self.config.get("project", {}).get("name", "deployx-app")
                }
                
                # Add build configuration if needed
                build_config = self.config.get("build", {})
                if build_config.get("command"):
                    config["buildCommand"] = build_config["command"]
                if build_config.get("output"):
                    config["outputDirectory"] = build_config["output"]
                    
                vercel_config.write_text(json.dumps(config, indent=2))
            
            # Run build if configured
            if build_command:
                result = subprocess.run(
                    build_command.split(),
                    cwd=self.project_path,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    return False, f"Build failed: {result.stderr}"
            
            return True, "Deployment prepared successfully"
            
        except Exception as e:
            return False, f"Preparation failed: {str(e)}"
    
    def execute_deployment(self, project_path: str, output_dir: str) -> DeploymentResult:
        """Execute deployment to Vercel"""
        try:
            # Use Vercel CLI if available, otherwise use API
            if self._has_vercel_cli():
                success, message, url = self._deploy_with_cli()
            else:
                success, message, url = self._deploy_with_api()
            
            return DeploymentResult(success=success, url=url, message=message)
                
        except Exception as e:
            return DeploymentResult(success=False, message=f"Deployment failed: {str(e)}")
    
    def _has_vercel_cli(self) -> bool:
        """Check if Vercel CLI is available"""
        try:
            subprocess.run(["vercel", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _deploy_with_cli(self) -> Tuple[bool, str, Optional[str]]:
        """Deploy using Vercel CLI"""
        try:
            # Set token for CLI
            env = os.environ.copy()
            env["VERCEL_TOKEN"] = self.token
            
            # Deploy with CLI
            result = subprocess.run(
                ["vercel", "--prod", "--yes"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode == 0:
                # Extract URL from output
                lines = result.stdout.strip().split('\n')
                url = None
                for line in lines:
                    if line.startswith('https://'):
                        url = line.strip()
                        break
                
                return True, "Deployment successful", url
            else:
                return False, f"CLI deployment failed: {result.stderr}", None
                
        except Exception as e:
            return False, f"CLI deployment error: {str(e)}", None
    
    def _deploy_with_api(self) -> Tuple[bool, str, Optional[str]]:
        """Deploy using Vercel API (simplified)"""
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            # Create deployment
            deployment_data = {
                "name": self.config.get("project", {}).get("name", "deployx-app"),
                "files": [],
                "projectSettings": {}
            }
            
            response = requests.post(
                f"{self.api_base}/v13/deployments",
                headers=headers,
                json=deployment_data
            )
            
            if response.status_code == 200:
                data = response.json()
                url = f"https://{data.get('url', '')}"
                return True, "Deployment successful", url
            else:
                return False, f"API deployment failed (HTTP {response.status_code})", None
                
        except Exception as e:
            return False, f"API deployment error: {str(e)}", None
    
    def get_status(self, deployment_id: Optional[str] = None) -> DeploymentStatus:
        """Get deployment status"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Get deployments
            response = requests.get(
                f"{self.api_base}/v6/deployments",
                headers=headers,
                params={"limit": 1}
            )
            
            if response.status_code == 200:
                deployments = response.json().get("deployments", [])
                if deployments:
                    deployment = deployments[0]
                    state = deployment.get("state", "unknown")
                    
                    status_map = {
                        "READY": "ready",
                        "BUILDING": "building", 
                        "ERROR": "error",
                        "CANCELED": "error"
                    }
                    
                    return DeploymentStatus(
                        status=status_map.get(state, "unknown"),
                        url=f"https://{deployment.get('url', '')}",
                        last_updated=deployment.get("createdAt"),
                        message=f"Vercel deployment {state.lower()}"
                    )
            
            return DeploymentStatus(status="unknown", message="No deployments found")
            
        except Exception as e:
            return DeploymentStatus(status="error", message=f"Status check failed: {str(e)}")
    
    def get_url(self) -> Optional[str]:
        """Get deployment URL"""
        status = self.get_status()
        return status.url