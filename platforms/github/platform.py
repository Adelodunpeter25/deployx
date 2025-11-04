"""
GitHub Pages deployment platform implementation.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from github import Github, GithubException
import requests

from utils.errors import retry_with_backoff, handle_auth_error, handle_github_api_error
from ..base import BasePlatform, DeploymentResult, DeploymentStatus
from ..env_interface import PlatformEnvInterface
from .cli_integration import GitHubCLIIntegration
from .git_utils import GitUtils
from .auto_creation import GitHubAutoCreation
from .deployment import GitHubDeployment
from .env_management import GitHubEnvManagement

class GitHubPlatform(BasePlatform, PlatformEnvInterface):
    """GitHub Pages deployment platform."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.repo_name = config.get('github', {}).get('repo')
        self.method = config.get('github', {}).get('method', 'branch')
        self.branch = config.get('github', {}).get('branch', 'gh-pages')
        self.github_client = None
        self.repo_obj = None
        
        # Initialize CLI integration first (needed by _get_token)
        self.cli_integration = GitHubCLIIntegration()
        
        # Now get token (which uses cli_integration)
        self.token = self._get_token()
        
        # Initialize other components
        self.auto_creation = GitHubAutoCreation(self.token) if self.token else None
        self.deployment = GitHubDeployment(self.repo_name, self.method, self.branch)
        self.env_management = None  # Initialized after validation
    
    def set_environment_variables(self, env_vars: Dict[str, str]) -> Tuple[bool, str]:
        """Set environment variables as GitHub repository secrets."""
        if not self.env_management:
            valid, _ = self.validate_credentials()
            if not valid:
                return False, "Invalid credentials"
        return self.env_management.set_environment_variables(env_vars)
    
    def get_environment_variables(self) -> Tuple[bool, Dict[str, str], str]:
        """Get environment variables (secret names only)."""
        if not self.env_management:
            valid, _ = self.validate_credentials()
            if not valid:
                return False, {}, "Invalid credentials"
        return self.env_management.get_environment_variables()
    
    def delete_environment_variable(self, key: str) -> Tuple[bool, str]:
        """Delete an environment variable (secret)."""
        if not self.env_management:
            valid, _ = self.validate_credentials()
            if not valid:
                return False, "Invalid credentials"
        return self.env_management.delete_environment_variable(key)
    
    def _get_token(self) -> Optional[str]:
        """Get GitHub token from CLI integration, file, or environment."""
        # Try CLI integration first
        if self.cli_integration.is_cli_available():
            token = self.cli_integration.get_token()
            if token:
                return token
        
        # Try .deployx_token file
        try:
            token_file = Path('.deployx_token')
            if token_file.exists():
                token = token_file.read_text().strip()
                if token:
                    return token
        except Exception:
            pass
        
        # Fallback to environment variable
        return os.getenv('GITHUB_TOKEN')
    
    @retry_with_backoff(max_retries=3)
    def validate_credentials(self) -> Tuple[bool, str]:
        """Validate GitHub token and repository access."""
        if not self.token:
            error = handle_auth_error("github", "No token provided")
            return False, error.message
        
        # Auto-create repository if needed
        if self.auto_creation and not self.repo_name:
            project_name = os.path.basename(os.getcwd())
            success, message, repo_full_name = self.auto_creation.auto_create_repository(project_name)
            
            if success and repo_full_name:
                self.repo_name = repo_full_name
                self.deployment.repo_name = repo_full_name
                self.logger.info(f"Auto-created repository: {repo_full_name}")
        
        if not self.repo_name:
            return False, "Repository name not configured"
        
        try:
            self.github_client = Github(self.token)
            
            # Validate token by fetching user info
            user = self.github_client.get_user()
            
            # Get repository and check write access
            self.repo_obj = self.github_client.get_repo(self.repo_name)
            
            # Initialize environment management
            self.env_management = GitHubEnvManagement(self.github_client, self.repo_name)
            
            # Check if user has write access
            try:
                permissions = self.repo_obj.get_collaborator_permission(user.login)
                if permissions not in ['admin', 'write']:
                    error = handle_auth_error("github", "Insufficient repository permissions")
                    return False, error.message
            except Exception:
                # If we can't check permissions, try a simple operation
                try:
                    self.repo_obj.get_contents("README.md")
                except Exception:
                    pass  # File might not exist, that's ok
            
            return True, f"GitHub credentials valid for user: {user.login}"
            
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            error = handle_auth_error("github", f"Network error: {str(e)}")
            return False, error.message
        except GithubException as e:
            error = handle_github_api_error(e)
            return False, error.message
    
    def get_deployment_status(self) -> DeploymentStatus:
        """Get current GitHub Pages deployment status"""
        try:
            if not self.repo_obj:
                # Try to initialize if not done yet
                valid, _ = self.validate_credentials()
                if not valid:
                    return DeploymentStatus(
                        status="error",
                        message="Invalid credentials",
                        url=None
                    )
            
            # Check if GitHub Pages is enabled
            try:
                pages = self.repo_obj.get_pages()
                return DeploymentStatus(
                    status="deployed" if pages.status == "built" else "building",
                    message=f"GitHub Pages status: {pages.status}",
                    url=pages.html_url
                )
            except GithubException as e:
                if e.status == 404:
                    return DeploymentStatus(
                        status="not_deployed",
                        message="GitHub Pages not enabled",
                        url=None
                    )
                raise
                
        except Exception as e:
            return DeploymentStatus(
                status="error",
                message=f"Failed to get deployment status: {str(e)}",
                url=None
            )
    
    def prepare_deployment(self, project_path: str, build_command: Optional[str], output_dir: str) -> Tuple[bool, str]:
        """Prepare for deployment by validating credentials and repository."""
        valid, message = self.validate_credentials()
        if not valid:
            return False, message
        
        # Check if repository exists and is accessible
        if not self.repo_obj:
            return False, "Repository not accessible"
        
        return True, "Ready for deployment"
    
    def execute_deployment(self, project_path: str, output_dir: str) -> DeploymentResult:
        """Execute deployment to GitHub Pages."""
        if self.method == "branch":
            return self.deployment.deploy_to_branch(project_path, output_dir)
        elif self.method == "docs":
            return self.deployment.deploy_to_docs_folder(project_path, output_dir)
        else:
            return DeploymentResult(
                success=False,
                message=f"Unknown deployment method: {self.method}",
                url=None,
                deployment_id=None
            )
    
    def get_status(self, deployment_id: Optional[str] = None) -> DeploymentStatus:
        """Get deployment status."""
        return self.get_deployment_status()
    
    def get_url(self) -> Optional[str]:
        """Get the deployment URL."""
        if not self.repo_name:
            return None
        
        parts = self.repo_name.split('/')
        if len(parts) != 2:
            return None
        
        username, repo = parts
        
        # Special case for username.github.io repositories
        if repo == f"{username}.github.io":
            return f"https://{username}.github.io"
        else:
            return f"https://{username}.github.io/{repo}"
