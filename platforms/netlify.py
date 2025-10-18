"""
Netlify deployment platform implementation
"""

import os
import requests
import subprocess
import zipfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from .base import BasePlatform, DeploymentResult, DeploymentStatus
from utils.errors import AuthenticationError

class NetlifyPlatform(BasePlatform):
    """Netlify deployment platform"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_base = "https://api.netlify.com/api/v1"
        self.project_path = config.get('project_path', '.')
        self.token = self._get_token()
        self.site_id = config.get("netlify", {}).get("site_id")
        
    def _get_token(self) -> str:
        """Get Netlify token from file or environment"""
        token_file = Path('.deployx_netlify_token')
        
        if token_file.exists():
            try:
                with open(token_file, 'r') as f:
                    return f.read().strip()
            except Exception:
                pass
            
        token = os.getenv("NETLIFY_TOKEN")
        if not token:
            raise AuthenticationError("Netlify token not found. Run 'deployx init' to configure.")
        return token
    
    def validate_credentials(self) -> Tuple[bool, str]:
        """Validate Netlify credentials"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.api_base}/user", headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                return True, f"Authenticated as {user_data.get('email', 'user')}"
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
                    cwd=self.project_path,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    return False, f"Build failed: {result.stderr}"
            
            # Check output directory exists
            output_dir = self.config.get("build", {}).get("output", "dist")
            output_path = Path(self.project_path) / output_dir
            
            if not output_path.exists():
                return False, f"Output directory '{output_dir}' not found"
            
            return True, "Deployment prepared successfully"
            
        except Exception as e:
            return False, f"Preparation failed: {str(e)}"
    
    def execute_deployment(self, project_path: str, output_dir: str) -> DeploymentResult:
        """Execute deployment to Netlify"""
        try:
            # Use Netlify CLI if available, otherwise use API
            if self._has_netlify_cli():
                success, message, url = self._deploy_with_cli()
            else:
                success, message, url = self._deploy_with_api()
            
            return DeploymentResult(success=success, url=url, message=message)
                
        except Exception as e:
            return DeploymentResult(success=False, message=f"Deployment failed: {str(e)}")
    
    def _has_netlify_cli(self) -> bool:
        """Check if Netlify CLI is available"""
        try:
            subprocess.run(["netlify", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _deploy_with_cli(self) -> Tuple[bool, str, Optional[str]]:
        """Deploy using Netlify CLI"""
        try:
            # Set token for CLI
            env = os.environ.copy()
            env["NETLIFY_AUTH_TOKEN"] = self.token
            
            # Build deploy command
            cmd = ["netlify", "deploy", "--prod"]
            
            output_dir = self.config.get("build", {}).get("output", "dist")
            cmd.extend(["--dir", output_dir])
            
            if self.site_id:
                cmd.extend(["--site", self.site_id])
            
            result = subprocess.run(
                cmd,
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
                    if "Live URL:" in line:
                        url = line.split("Live URL:")[-1].strip()
                        break
                    elif line.startswith('https://'):
                        url = line.strip()
                        break
                
                return True, "Deployment successful", url
            else:
                return False, f"CLI deployment failed: {result.stderr}", None
                
        except Exception as e:
            return False, f"CLI deployment error: {str(e)}", None
    
    def _deploy_with_api(self) -> Tuple[bool, str, Optional[str]]:
        """Deploy using Netlify API"""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Create site if no site_id
            if not self.site_id:
                site_data = {
                    "name": self.config.get("project", {}).get("name", "deployx-app")
                }
                response = requests.post(f"{self.api_base}/sites", headers=headers, json=site_data)
                if response.status_code == 201:
                    self.site_id = response.json()["id"]
                else:
                    return False, f"Failed to create site (HTTP {response.status_code})", None
            
            # Create zip of output directory
            output_dir = self.config.get("build", {}).get("output", "dist")
            zip_path = self._create_deployment_zip(output_dir)
            
            # Upload deployment
            with open(zip_path, 'rb') as f:
                headers["Content-Type"] = "application/zip"
                response = requests.post(
                    f"{self.api_base}/sites/{self.site_id}/deploys",
                    headers=headers,
                    data=f
                )
            
            # Clean up zip file
            os.unlink(zip_path)
            
            if response.status_code == 200:
                data = response.json()
                url = data.get("ssl_url") or data.get("url")
                return True, "Deployment successful", url
            else:
                return False, f"API deployment failed (HTTP {response.status_code})", None
                
        except Exception as e:
            return False, f"API deployment error: {str(e)}", None
    
    def _create_deployment_zip(self, output_dir: str) -> str:
        """Create zip file of output directory"""
        output_path = Path(self.project_path) / output_dir
        zip_path = Path(self.project_path) / "netlify-deploy.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in output_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(output_path)
                    zipf.write(file_path, arcname)
        
        return str(zip_path)
    
    def get_status(self, deployment_id: Optional[str] = None) -> DeploymentStatus:
        """Get deployment status"""
        try:
            if not self.site_id:
                return DeploymentStatus(status="unknown", message="No site ID configured")
                
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Get latest deployment
            response = requests.get(
                f"{self.api_base}/sites/{self.site_id}/deploys",
                headers=headers,
                params={"per_page": 1}
            )
            
            if response.status_code == 200:
                deploys = response.json()
                if deploys:
                    deploy = deploys[0]
                    state = deploy.get("state", "unknown")
                    
                    status_map = {
                        "ready": "ready",
                        "building": "building",
                        "error": "error",
                        "failed": "error"
                    }
                    
                    return DeploymentStatus(
                        status=status_map.get(state, "unknown"),
                        url=deploy.get("ssl_url") or deploy.get("url"),
                        last_updated=deploy.get("created_at"),
                        message=f"Netlify deployment {state}"
                    )
            
            return DeploymentStatus(status="unknown", message="No deployments found")
            
        except Exception as e:
            return DeploymentStatus(status="error", message=f"Status check failed: {str(e)}")
    
    def get_url(self) -> Optional[str]:
        """Get deployment URL"""
        status = self.get_status()
        return status.url