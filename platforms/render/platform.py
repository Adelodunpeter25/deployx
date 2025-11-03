"""
Render deployment platform implementation with auto-configuration.
"""

import os
import requests
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from ..base import BasePlatform, DeploymentResult, DeploymentStatus
from ..env_interface import PlatformEnvInterface
from .api import RenderAPIClient
from .detector import RenderServiceDetector
from utils.errors import AuthenticationError
from utils.config import Config
from core.logging import get_logger

class RenderPlatform(BasePlatform, PlatformEnvInterface):
    """Render deployment platform with auto-service creation."""
    
    def __init__(self, config: Dict[str, Any]):
        BasePlatform.__init__(self, config)
        PlatformEnvInterface.__init__(self)
        self.api_base = "https://api.render.com/v1"
        self.project_path = config.get('project_path', '.')
        self.token = self._get_token()
        self.service_id = config.get("service_id")
        self.api_client = RenderAPIClient(self.token) if self.token else None
        self.logger = get_logger(__name__)
        
    def _get_token(self) -> str:
        """Get Render token from file or environment."""
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
        """Validate Render credentials and auto-configure service if needed."""
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.api_base}/owners", headers=headers)
            
            if response.status_code == 200:
                owners = response.json()
                username = owners[0].get('name', 'user') if owners else 'user'
                
                # Auto-configure service if service_id is missing
                if not self.service_id:
                    self.logger.info("No service ID found, attempting auto-configuration")
                    success, message = self._auto_configure_service()
                    if not success:
                        return False, f"Auto-configuration failed: {message}"
                
                return True, f"Authenticated as {username}"
            else:
                return False, f"Authentication failed: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def _auto_configure_service(self) -> Tuple[bool, str]:
        """Auto-configure Render service for the project."""
        try:
            # Get project information
            config = Config(self.project_path)
            config_data = config.load()
            
            project_name = config_data.get("project", {}).get("name", Path(self.project_path).name)
            project_type = config_data.get("project", {}).get("type", "static")
            
            # Detect service type and configuration
            service_type, build_command, publish_path = RenderServiceDetector.detect_service_type(
                self.project_path, project_type
            )
            
            # Get existing services to avoid name conflicts
            success, existing_services, error = self.api_client.list_services()
            if not success:
                return False, f"Failed to list existing services: {error}"
            
            # Generate unique service name
            service_name = RenderServiceDetector.generate_service_name(project_name, existing_services)
            
            # Get repository URL
            repo_url = self._get_git_repo_url() or f"https://github.com/user/{project_name}"
            
            # Create the service
            self.logger.info(f"Creating {service_type} service: {service_name}")
            success, service, error = self.api_client.create_service(
                name=service_name,
                service_type=service_type,
                repo_url=repo_url,
                build_command=build_command,
                publish_path=publish_path
            )
            
            if success:
                # Update configuration with new service ID
                self.service_id = service.id
                self._update_config_with_service_id(service.id)
                
                self.logger.info(f"Service created successfully: {service.id}")
                return True, f"Service '{service_name}' created with ID: {service.id}"
            else:
                return False, error
                
        except Exception as e:
            self.logger.error(f"Auto-configuration failed: {e}")
            return False, str(e)
    
    def _update_config_with_service_id(self, service_id: str):
        """Update configuration file with new service ID."""
        try:
            config = Config(self.project_path)
            config_data = config.load()
            
            # Ensure render section exists
            if "render" not in config_data:
                config_data["render"] = {}
            
            # Update service ID
            config_data["render"]["service_id"] = service_id
            
            # Save updated configuration
            config.save(config_data)
            self.logger.info(f"Configuration updated with service ID: {service_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to update configuration: {e}")
    
    def _get_git_repo_url(self) -> Optional[str]:
        """Get Git repository URL from project."""
        try:
            import git
            repo = git.Repo(self.project_path)
            origin = repo.remote('origin')
            return origin.url
        except Exception:
            return None
    
    def prepare_deployment(self, project_path: str, build_command: Optional[str], output_dir: str) -> Tuple[bool, str]:
        """Prepare deployment files."""
        try:
            # Run build if configured
            if build_command:
                result = subprocess.run(
                    build_command,
                    cwd=project_path,
                    shell=True,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    return False, f"Build failed: {result.stderr}"
            
            return True, "Deployment prepared successfully"
            
        except Exception as e:
            return False, f"Preparation failed: {str(e)}"
    
    def execute_deployment(self, project_path: str, output_dir: str) -> DeploymentResult:
        """Execute deployment to Render."""
        try:
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
    
    def set_environment_variables(self, env_vars: Dict[str, str]) -> Tuple[bool, str]:
        """Set environment variables for Render service."""
        try:
            if not self.service_id:
                return False, "No service ID configured"
            
            # Validate variables
            is_valid, error_msg = self.validate_environment_variables(env_vars)
            if not is_valid:
                return False, error_msg
            
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            # Convert to Render API format
            env_vars_list = [{"key": key, "value": value} for key, value in env_vars.items()]
            
            response = requests.patch(
                f"{self.api_base}/services/{self.service_id}",
                json={"envVars": env_vars_list},
                headers=headers
            )
            
            if response.status_code == 200:
                return True, f"Successfully set {len(env_vars)} environment variables"
            else:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("message", f"HTTP {response.status_code}")
                return False, f"Failed to set environment variables: {error_msg}"
                
        except Exception as e:
            error_msg = f"Failed to set Render environment variables: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_environment_variables(self) -> Tuple[bool, Dict[str, str], str]:
        """Get environment variables from Render service."""
        try:
            if not self.service_id:
                return False, {}, "No service ID configured"
            
            headers = {"Authorization": f"Bearer {self.token}"}
            
            response = requests.get(
                f"{self.api_base}/services/{self.service_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                service_data = response.json()
                env_vars = {}
                
                # Extract environment variables
                for env_var in service_data.get("envVars", []):
                    env_vars[env_var["key"]] = env_var["value"]
                
                return True, env_vars, ""
            else:
                error_msg = f"Failed to get service details: HTTP {response.status_code}"
                return False, {}, error_msg
                
        except Exception as e:
            error_msg = f"Failed to get Render environment variables: {str(e)}"
            self.logger.error(error_msg)
            return False, {}, error_msg
    
    def delete_environment_variable(self, key: str) -> Tuple[bool, str]:
        """Delete an environment variable from Render service."""
        try:
            # Get current variables
            success, current_vars, error = self.get_environment_variables()
            if not success:
                return False, f"Failed to get current variables: {error}"
            
            if key not in current_vars:
                return False, f"Environment variable '{key}' not found"
            
            # Remove the key and update
            del current_vars[key]
            return self.set_environment_variables(current_vars)
            
        except Exception as e:
            error_msg = f"Failed to delete Render environment variable {key}: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_deployment_status(self) -> DeploymentStatus:
        """Get deployment status."""
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
