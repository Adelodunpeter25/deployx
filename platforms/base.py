"""
Base platform interface for DeployX.

Defines the abstract interface that all deployment platforms must implement.
Provides common data structures for deployment results and status.

To add a new platform:
1. Create a new file in platforms/ directory
2. Subclass BasePlatform
3. Implement all abstract methods
4. Register in platforms/factory.py

Example:
    >>> from platforms.base import BasePlatform, DeploymentResult
    >>> class MyPlatform(BasePlatform):
    ...     def validate_credentials(self):
    ...         return True, "Valid"
    ...     # ... implement other methods
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class DeploymentResult:
    """
    Result of a deployment operation.
    
    Attributes:
        success: Whether deployment succeeded
        url: Live URL of deployed site (if available)
        message: Human-readable status message
        deployment_id: Platform-specific deployment identifier
    
    Example:
        >>> result = DeploymentResult(
        ...     success=True,
        ...     url="https://myapp.github.io",
        ...     message="Deployment successful"
        ... )
    """
    success: bool
    url: Optional[str] = None
    message: str = ""
    deployment_id: Optional[str] = None


@dataclass
class DeploymentStatus:
    """
    Current status of a deployment.
    
    Attributes:
        status: Status string ("building", "ready", "error", "unknown")
        url: Live URL if deployment is ready
        last_updated: ISO timestamp of last update
        message: Additional status information
    
    Example:
        >>> status = DeploymentStatus(
        ...     status="ready",
        ...     url="https://myapp.com",
        ...     message="Deployment is live"
        ... )
    """
    status: str  # "building", "ready", "error", "unknown"
    url: Optional[str] = None
    last_updated: Optional[str] = None
    message: str = ""


class BasePlatform(ABC):
    """
    Abstract base class for all deployment platforms.
    
    All platform implementations must inherit from this class and
    implement all abstract methods. Provides common functionality
    for configuration access.
    
    Attributes:
        config: Platform-specific configuration dictionary
        platform_name: Name of the platform (auto-derived from class name)
    
    Example:
        >>> class GitHubPlatform(BasePlatform):
        ...     def validate_credentials(self):
        ...         # Implementation
        ...         pass
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize platform with configuration.
        
        Args:
            config: Platform-specific configuration dictionary
        """
        self.config = config
        self.platform_name = self.__class__.__name__.lower().replace('platform', '')
    
    @abstractmethod
    def validate_credentials(self) -> Tuple[bool, str]:
        """
        Validate platform credentials/API tokens.
        
        Should check that provided credentials are valid and have
        necessary permissions for deployment.
        
        Returns:
            Tuple of (is_valid, message):
                - is_valid: True if credentials are valid
                - message: Success message or error description
        
        Example:
            >>> valid, msg = platform.validate_credentials()
            >>> if not valid:
            ...     print(f"Auth failed: {msg}")
        """
        pass
    
    @abstractmethod
    def prepare_deployment(self, project_path: str, build_command: Optional[str], 
                          output_dir: str) -> Tuple[bool, str]:
        """
        Prepare deployment by running builds and checking files.
        
        Should execute build command if provided, verify output
        directory exists, and check that necessary files are present.
        
        Args:
            project_path: Path to project directory
            build_command: Command to build project (None if no build needed)
            output_dir: Directory containing built files
            
        Returns:
            Tuple of (success, message):
                - success: True if preparation successful
                - message: Success message or error description
        
        Example:
            >>> success, msg = platform.prepare_deployment(
            ...     "./my-app", "npm run build", "build"
            ... )
        """
        pass
    
    @abstractmethod
    def execute_deployment(self, project_path: str, output_dir: str) -> DeploymentResult:
        """
        Execute the actual deployment.
        
        Should upload files to platform and trigger deployment process.
        This is the main deployment logic.
        
        Args:
            project_path: Path to project directory
            output_dir: Directory containing files to deploy
            
        Returns:
            DeploymentResult with success status, URL, and message
        
        Example:
            >>> result = platform.execute_deployment("./my-app", "build")
            >>> if result.success:
            ...     print(f"Deployed to {result.url}")
        """
        pass
    
    @abstractmethod
    def get_status(self, deployment_id: Optional[str] = None) -> DeploymentStatus:
        """
        Get current deployment status.
        
        Should query platform API to get current status of deployment.
        Can check specific deployment by ID or latest deployment.
        
        Args:
            deployment_id: Optional deployment ID to check specific deployment
            
        Returns:
            DeploymentStatus with current status information
        
        Example:
            >>> status = platform.get_status()
            >>> print(f"Status: {status.status}")
        """
        pass
    
    @abstractmethod
    def get_url(self) -> Optional[str]:
        """
        Get the live site URL.
        
        Should return the URL where the deployed site is accessible.
        Returns None if URL cannot be determined.
        
        Returns:
            Live site URL or None if not available
        
        Example:
            >>> url = platform.get_url()
            >>> if url:
            ...     print(f"Visit: {url}")
        """
        pass
    
    def get_platform_name(self) -> str:
        """
        Get platform name.
        
        Returns:
            Platform name string (e.g., "github", "vercel")
        """
        return self.platform_name
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key to retrieve
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        
        Example:
            >>> repo = platform.get_config("repo", "unknown/repo")
        """
        return self.config.get(key, default)
