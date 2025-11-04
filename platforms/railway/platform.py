"""
Railway deployment platform implementation with complete auto-setup.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import requests

from utils.errors import retry_with_backoff, handle_auth_error, AuthenticationError
from ..base import BasePlatform, DeploymentResult, DeploymentStatus
from .cli_integration import RailwayCLIIntegration
from .api_integration import RailwayAPIIntegration
from .auto_creation import RailwayAutoCreation

class RailwayPlatform(BasePlatform):
    """Railway deployment platform with complete auto-setup."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Handle both full config and platform-specific config
        if 'railway' in config:
            railway_config = config.get('railway', {})
        else:
            railway_config = config
        
        self.project_id = railway_config.get('project_id')
        self.service_id = railway_config.get('service_id')
        self.environment_id = railway_config.get('environment_id')
        self.use_cli = railway_config.get('use_cli', True)
        
        # Initialize components
        self.cli_integration = RailwayCLIIntegration()
        
        # Get token and initialize other components
        self.token = self._get_token()
        self.api_integration = RailwayAPIIntegration(self.token) if self.token else None
        self.auto_creation = RailwayAutoCreation(self.token, self.use_cli) if self.token else None
    
    def _get_token(self) -> Optional[str]:
        """Get Railway token from CLI, file, or environment."""
        # Try CLI integration first
        if self.cli_integration.is_cli_available():
            token = self.cli_integration.get_token()
            if token:
                return token
        
        # Try .deployx_railway_token file
        try:
            token_file = Path('.deployx_railway_token')
            if token_file.exists():
                token = token_file.read_text().strip()
                if token:
                    return token
        except Exception:
            pass
        
        # Fallback to environment variable
        return os.getenv('RAILWAY_TOKEN')
    
    @retry_with_backoff(max_retries=3)
    def validate_credentials(self) -> Tuple[bool, str]:
        """Validate Railway token and setup complete project if needed."""
        # Refresh token (in case it was updated)
        self.token = self._get_token()
        
        if not self.token:
            error = handle_auth_error("railway", "No token provided")
            return False, error.message
        
        # Initialize components if not available
        if not self.api_integration:
            self.api_integration = RailwayAPIIntegration(self.token)
        if not self.auto_creation:
            self.auto_creation = RailwayAutoCreation(self.token, self.use_cli)
        
        # Validate token
        valid, message, user_data = self.api_integration.validate_token()
        if not valid:
            return False, message
        
        # Auto-create complete setup if needed
        if self.auto_creation and not self.project_id:
            project_name = os.path.basename(os.getcwd())
            success, setup_message, setup_info = self.auto_creation.auto_create_complete_setup(project_name)
            
            if success and setup_info:
                self.project_id = setup_info.get('project_id')
                self.service_id = setup_info.get('service_id')
                self.environment_id = setup_info.get('environment_id')
                self.logger.info(f"Auto-created Railway setup: {setup_info}")
            elif not success:
                return False, f"Setup creation failed: {setup_message}"
        
        return True, message
    
    def prepare_deployment(self, project_path: str, build_command: Optional[str], output_dir: str) -> Tuple[bool, str]:
        """Prepare for deployment by validating credentials and setup."""
        valid, message = self.validate_credentials()
        if not valid:
            return False, message
        
        # Ensure we have project and service setup
        if not self.project_id:
            return False, "No Railway project configured"
        
        if not self.service_id:
            return False, "No Railway service configured"
        
        return True, "Ready for deployment"
    
    def execute_deployment(self, project_path: str, output_dir: str) -> DeploymentResult:
        """Execute deployment to Railway."""
        try:
            # Try CLI deployment first if available and linked
            if self.use_cli and self.cli_integration.is_cli_available():
                return self._deploy_via_cli(project_path)
            
            # Fallback to API deployment
            elif self.api_integration and self.service_id and self.environment_id:
                return self._deploy_via_api()
            
            else:
                return DeploymentResult(
                    success=False,
                    message="No deployment method available or incomplete setup",
                    url=None,
                    deployment_id=None
                )
                
        except Exception as e:
            return DeploymentResult(
                success=False,
                message=f"Deployment failed: {str(e)}",
                url=None,
                deployment_id=None
            )
    
    def _deploy_via_cli(self, project_path: str) -> DeploymentResult:
        """Deploy using Railway CLI."""
        # Link project if needed
        if self.project_id:
            link_success, link_message = self.cli_integration.link_project(self.project_id, project_path)
            if not link_success:
                return DeploymentResult(
                    success=False,
                    message=f"Failed to link project: {link_message}",
                    url=None,
                    deployment_id=None
                )
        
        # Deploy
        success, message, url = self.cli_integration.deploy_project(project_path)
        
        return DeploymentResult(
            success=success,
            message=message,
            url=url,
            deployment_id=None
        )
    
    def _deploy_via_api(self) -> DeploymentResult:
        """Deploy using Railway API."""
        success, message, deployment_id = self.api_integration.create_deployment(
            self.service_id, self.environment_id
        )
        
        # Generate URL (Railway URLs are typically project-based)
        url = None
        if success and self.project_id:
            # Railway URLs are usually in format: https://{service}.railway.app
            # But we can't predict the exact URL without additional API calls
            url = f"https://railway.app/project/{self.project_id}"
        
        return DeploymentResult(
            success=success,
            message=message,
            url=url,
            deployment_id=deployment_id
        )
    
    def get_deployment_status(self) -> DeploymentStatus:
        """Get current deployment status."""
        try:
            if self.project_id and self.api_integration:
                success, project_info, message = self.api_integration.get_project_info(self.project_id)
                if success and project_info:
                    return DeploymentStatus(
                        status="deployed",
                        message=f"Railway project: {project_info.get('name')}",
                        url=f"https://railway.app/project/{self.project_id}"
                    )
                else:
                    return DeploymentStatus(
                        status="error",
                        message=f"Failed to get project info: {message}",
                        url=None
                    )
            else:
                return DeploymentStatus(
                    status="not_deployed",
                    message="No Railway project configured",
                    url=None
                )
        except Exception as e:
            return DeploymentStatus(
                status="error",
                message=f"Failed to get status: {str(e)}",
                url=None
            )
    
    def get_status(self, deployment_id: Optional[str] = None) -> DeploymentStatus:
        """Get deployment status."""
        return self.get_deployment_status()
    
    def get_url(self) -> Optional[str]:
        """Get the deployment URL."""
        if self.project_id:
            return f"https://railway.app/project/{self.project_id}"
        return None
