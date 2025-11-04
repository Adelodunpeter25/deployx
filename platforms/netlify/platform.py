"""
Netlify deployment platform implementation with Phase 2 features.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import requests

from utils.errors import retry_with_backoff, handle_auth_error, AuthenticationError
from ..base import BasePlatform, DeploymentResult, DeploymentStatus
from .cli_integration import NetlifyCLIIntegration
from .api_integration import NetlifyAPIIntegration
from .auto_creation import NetlifyAutoCreation

class NetlifyPlatform(BasePlatform):
    """Netlify deployment platform with CLI integration and auto-creation."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Handle both full config and platform-specific config
        if 'netlify' in config:
            netlify_config = config.get('netlify', {})
        else:
            netlify_config = config
        
        self.site_id = netlify_config.get('site_id')
        self.custom_domain = netlify_config.get('custom_domain')
        self.use_cli = netlify_config.get('use_cli', True)
        
        # Initialize components
        self.cli_integration = NetlifyCLIIntegration()
        
        # Get token and initialize other components
        self.token = self._get_token()
        self.api_integration = NetlifyAPIIntegration(self.token) if self.token else None
        self.auto_creation = NetlifyAutoCreation(self.token, self.use_cli) if self.token else None
    
    def _get_token(self) -> Optional[str]:
        """Get Netlify token from CLI, file, or environment."""
        # Try CLI integration first
        if self.cli_integration.is_cli_available():
            token = self.cli_integration.get_token()
            if token:
                return token
        
        # Try .deployx_netlify_token file
        try:
            token_file = Path('.deployx_netlify_token')
            if token_file.exists():
                token = token_file.read_text().strip()
                if token:
                    return token
        except Exception:
            pass
        
        # Fallback to environment variable
        return os.getenv('NETLIFY_TOKEN')
    
    @retry_with_backoff(max_retries=3)
    def validate_credentials(self) -> Tuple[bool, str]:
        """Validate Netlify token and setup site if needed."""
        # Refresh token (in case it was updated)
        self.token = self._get_token()
        
        if not self.token:
            error = handle_auth_error("netlify", "No token provided")
            return False, error.message
        
        # Initialize components if not available
        if not self.api_integration:
            self.api_integration = NetlifyAPIIntegration(self.token)
        if not self.auto_creation:
            self.auto_creation = NetlifyAutoCreation(self.token, self.use_cli)
        
        # Validate token
        valid, message, user_data = self.api_integration.validate_token()
        if not valid:
            return False, message
        
        # Auto-create site if needed
        if self.auto_creation and not self.site_id:
            site_name = os.path.basename(os.getcwd())
            success, site_message, site_id = self.auto_creation.auto_create_site(
                site_name, ".", self.custom_domain
            )
            
            if success and site_id:
                self.site_id = site_id
                self.logger.info(f"Auto-created Netlify site: {site_name}")
            elif not success:
                return False, f"Site creation failed: {site_message}"
        
        return True, message
    
    def prepare_deployment(self, project_path: str, build_command: Optional[str], output_dir: str) -> Tuple[bool, str]:
        """Prepare for deployment by validating credentials and site."""
        valid, message = self.validate_credentials()
        if not valid:
            return False, message
        
        # Check if build output exists
        build_path = Path(project_path) / output_dir
        if not build_path.exists():
            return False, f"Build output directory not found: {build_path}"
        
        # Ensure we have a site
        if not self.site_id:
            return False, "No Netlify site configured"
        
        return True, "Ready for deployment"
    
    def execute_deployment(self, project_path: str, output_dir: str) -> DeploymentResult:
        """Execute deployment to Netlify."""
        try:
            # Try CLI deployment first if available and linked
            if self.use_cli and self.cli_integration.is_cli_available():
                return self._deploy_via_cli(project_path, output_dir)
            
            # Fallback to API deployment
            elif self.api_integration and self.site_id:
                return self._deploy_via_api(project_path, output_dir)
            
            else:
                return DeploymentResult(
                    success=False,
                    message="No deployment method available or site not configured",
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
    
    def _deploy_via_cli(self, project_path: str, output_dir: str) -> DeploymentResult:
        """Deploy using Netlify CLI."""
        # Link site if needed
        if self.site_id:
            link_success, link_message = self.cli_integration.link_site(self.site_id, project_path)
            if not link_success:
                return DeploymentResult(
                    success=False,
                    message=f"Failed to link site: {link_message}",
                    url=None,
                    deployment_id=None
                )
        
        # Deploy
        success, message, url = self.cli_integration.deploy_site(project_path, output_dir)
        
        return DeploymentResult(
            success=success,
            message=message,
            url=url,
            deployment_id=None
        )
    
    def _deploy_via_api(self, project_path: str, output_dir: str) -> DeploymentResult:
        """Deploy using Netlify API."""
        success, message, url = self.api_integration.deploy_site(
            self.site_id, project_path, output_dir
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
            if self.site_id and self.api_integration:
                success, status, url = self.api_integration.get_deployment_status(self.site_id)
                if success:
                    status_map = {
                        "ready": "deployed",
                        "building": "building", 
                        "error": "error",
                        "no_deploys": "not_deployed"
                    }
                    mapped_status = status_map.get(status, status)
                    
                    return DeploymentStatus(
                        status=mapped_status,
                        message=f"Netlify deployment: {status}",
                        url=url
                    )
                else:
                    return DeploymentStatus(
                        status="error",
                        message="Failed to get deployment status",
                        url=None
                    )
            else:
                return DeploymentStatus(
                    status="not_deployed",
                    message="No Netlify site configured",
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
        if self.site_id and self.api_integration:
            success, site_data, _ = self.api_integration.get_site_info(self.site_id)
            if success and site_data:
                return site_data.get('url')
        return None
