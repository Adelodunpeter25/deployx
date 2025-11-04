"""
Vercel deployment platform implementation.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from utils.errors import retry_with_backoff, handle_auth_error
from ..base import BasePlatform, DeploymentResult, DeploymentStatus
from .cli_integration import VercelCLIIntegration
from .api_integration import VercelAPIIntegration
from .auto_creation import VercelAutoCreation

class VercelPlatform(BasePlatform):
    """Vercel deployment platform with CLI and API integration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Handle both full config and platform-specific config
        if 'vercel' in config:
            vercel_config = config.get('vercel', {})
        else:
            vercel_config = config
        
        self.project_name = vercel_config.get('project')
        self.framework = vercel_config.get('framework')
        self.use_cli = vercel_config.get('use_cli', True)
        
        # Initialize components
        self.cli_integration = VercelCLIIntegration()
        
        # Get token and initialize other components
        self.token = self._get_token()
        self.api_integration = VercelAPIIntegration(self.token) if self.token else None
        self.auto_creation = VercelAutoCreation(self.token, self.use_cli) if self.token else None
    
    def _get_token(self) -> Optional[str]:
        """Get Vercel token from CLI, file, or environment."""
        # Try CLI integration first
        if self.cli_integration.is_cli_available():
            token = self.cli_integration.get_token()
            if token:
                return token
        
        # Try .deployx_vercel_token file
        try:
            token_file = Path('.deployx_vercel_token')
            if token_file.exists():
                token = token_file.read_text().strip()
                if token:
                    return token
        except Exception:
            pass
        
        # Fallback to environment variable
        return os.getenv('VERCEL_TOKEN')
    
    @retry_with_backoff(max_retries=3)
    def validate_credentials(self) -> Tuple[bool, str]:
        """Validate Vercel token and access."""
        # Refresh token (in case it was updated)
        self.token = self._get_token()
        
        if not self.token:
            error = handle_auth_error("vercel", "No token provided")
            return False, error.message
        
        # Initialize components if not available
        if not self.api_integration:
            self.api_integration = VercelAPIIntegration(self.token)
        if not self.auto_creation:
            self.auto_creation = VercelAutoCreation(self.token, self.use_cli)
        
        # Auto-create project if needed
        if self.auto_creation and not self.project_name:
            project_name = os.path.basename(os.getcwd())
            success, message, project_url = self.auto_creation.auto_create_project(
                project_name, ".", self.framework
            )
            
            if success and project_url:
                self.project_name = project_name
                self.logger.info(f"Auto-created Vercel project: {project_name}")
            elif not success:
                return False, f"Project creation failed: {message}"
        
        # Validate token by listing projects
        try:
            if self.api_integration:
                success, projects, message = self.api_integration.list_projects()
                if success:
                    return True, f"Vercel credentials valid - {len(projects)} projects accessible"
                else:
                    return False, f"Token validation failed: {message}"
            else:
                return False, "No API integration available"
                
        except Exception as e:
            return False, f"Credential validation failed: {str(e)}"
    
    def prepare_deployment(self, project_path: str, build_command: Optional[str], output_dir: str) -> Tuple[bool, str]:
        """Prepare for deployment by validating credentials."""
        valid, message = self.validate_credentials()
        if not valid:
            return False, message
        
        # Check if build output exists
        build_path = Path(project_path) / output_dir
        if not build_path.exists():
            return False, f"Build output directory not found: {build_path}"
        
        return True, "Ready for deployment"
    
    def execute_deployment(self, project_path: str, output_dir: str) -> DeploymentResult:
        """Execute deployment to Vercel."""
        try:
            # Try CLI deployment first if available
            if self.use_cli and self.cli_integration.is_cli_available():
                return self._deploy_via_cli(project_path)
            
            # Fallback to API deployment
            elif self.api_integration:
                return self._deploy_via_api(project_path, output_dir)
            
            else:
                return DeploymentResult(
                    success=False,
                    message="No deployment method available",
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
        """Deploy using Vercel CLI."""
        success, message, url = self.cli_integration.deploy_project(project_path)
        
        return DeploymentResult(
            success=success,
            message=message,
            url=url,
            deployment_id=None
        )
    
    def _deploy_via_api(self, project_path: str, output_dir: str) -> DeploymentResult:
        """Deploy using Vercel API."""
        # Upload files
        success, message, files_data = self.api_integration.upload_files(project_path, output_dir)
        if not success:
            return DeploymentResult(
                success=False,
                message=f"File upload failed: {message}",
                url=None,
                deployment_id=None
            )
        
        # Create deployment
        success, message, url = self.api_integration.create_deployment(
            self.project_name or "deployx-project", files_data
        )
        
        return DeploymentResult(
            success=success,
            message=message,
            url=url,
            deployment_id=None
        )
    
    def get_deployment_status(self) -> DeploymentStatus:
        """Get current deployment status."""
        try:
            if self.project_name:
                return DeploymentStatus(
                    status="deployed",
                    message=f"Vercel project: {self.project_name}",
                    url=f"https://{self.project_name}.vercel.app"
                )
            else:
                return DeploymentStatus(
                    status="not_deployed",
                    message="No Vercel project configured",
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
        if self.project_name:
            return f"https://{self.project_name}.vercel.app"
        return None
