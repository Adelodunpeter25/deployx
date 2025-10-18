from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class DeploymentResult:
    """Result of a deployment operation"""
    success: bool
    url: Optional[str] = None
    message: str = ""
    deployment_id: Optional[str] = None

@dataclass
class DeploymentStatus:
    """Status of a deployment"""
    status: str  # "building", "ready", "error", "unknown"
    url: Optional[str] = None
    last_updated: Optional[str] = None
    message: str = ""

class BasePlatform(ABC):
    """Abstract base class for all deployment platforms"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.platform_name = self.__class__.__name__.lower().replace('platform', '')
    
    @abstractmethod
    def validate_credentials(self) -> Tuple[bool, str]:
        """
        Validate platform credentials/API tokens
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def prepare_deployment(self, project_path: str, build_command: Optional[str], output_dir: str) -> Tuple[bool, str]:
        """
        Prepare deployment by running builds and checking files
        
        Args:
            project_path: Path to project directory
            build_command: Command to build project (if any)
            output_dir: Directory containing built files
            
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        pass
    
    @abstractmethod
    def execute_deployment(self, project_path: str, output_dir: str) -> DeploymentResult:
        """
        Execute the actual deployment
        
        Args:
            project_path: Path to project directory
            output_dir: Directory containing files to deploy
            
        Returns:
            DeploymentResult: Result of deployment operation
        """
        pass
    
    @abstractmethod
    def get_status(self, deployment_id: Optional[str] = None) -> DeploymentStatus:
        """
        Get deployment status
        
        Args:
            deployment_id: Optional deployment ID to check specific deployment
            
        Returns:
            DeploymentStatus: Current deployment status
        """
        pass
    
    @abstractmethod
    def get_url(self) -> Optional[str]:
        """
        Get the live site URL
        
        Returns:
            Optional[str]: Live site URL or None if not available
        """
        pass
    
    def get_platform_name(self) -> str:
        """Get platform name"""
        return self.platform_name
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)