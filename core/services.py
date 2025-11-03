"""
Business logic services for DeployX operations.

This module contains the core business logic services that handle
deployment operations, project initialization, and status checking.
It separates business logic from CLI presentation, making the code
more testable and maintainable.

Services:
    - DeploymentService: Handles deployment operations
    - InitService: Handles project initialization
    - StatusService: Handles deployment status checking

All services use async patterns for better performance and
non-blocking operations where appropriate.
"""
import asyncio
from pathlib import Path
from typing import Optional, Tuple
from .logging import get_logger
from .models import DeployXConfig
from utils.config import Config
from platforms.factory import get_platform
from detectors.project import detect_project
from commands.env_config import EnvConfigurator

logger = get_logger(__name__)

class DeploymentService:
    """
    Service for handling deployment operations.
    
    Manages the complete deployment workflow including configuration
    validation, credential checking, build preparation, and deployment
    execution. Provides both dry-run and actual deployment capabilities.
    
    Attributes:
        project_path: Path to the project directory
        config: Configuration manager instance
        logger: Logger instance for this service
    """
    
    def __init__(self, project_path: str = "."):
        """
        Initialize deployment service.
        
        Args:
            project_path: Path to project directory (default: current directory)
        """
        self.project_path = Path(project_path)
        self.config = Config(str(self.project_path))
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
    
    async def validate_config(self) -> Tuple[bool, Optional[DeployXConfig], Optional[str]]:
        """
        Validate configuration using Pydantic models.
        
        Loads the configuration file and validates it against the
        Pydantic schema, ensuring all required fields are present
        and properly formatted.
        
        Returns:
            Tuple containing:
                - success: True if validation passed
                - config: Validated configuration object (None if failed)
                - error: Error message (None if successful)
        """
        try:
            if not self.config.exists():
                return False, None, "No configuration found"
            
            config_data = self.config.load()
            validated_config = DeployXConfig(**config_data)
            self.logger.info("Configuration validation successful")
            return True, validated_config, None
            
        except Exception as e:
            error_msg = f"Configuration validation failed: {str(e)}"
            self.logger.error(error_msg)
            return False, None, error_msg
    
    async def deploy(self, force: bool = False, dry_run: bool = False) -> Tuple[bool, str]:
        """
        Execute deployment asynchronously.
        
        Performs the complete deployment workflow including configuration
        validation, credential checking, build preparation, and deployment
        execution. Supports both dry-run mode and forced deployment.
        
        Args:
            force: Skip confirmation prompts if True
            dry_run: Only simulate deployment without executing if True
            
        Returns:
            Tuple containing:
                - success: True if deployment succeeded
                - message: Success message or error description
        """
        self.logger.info(f"Starting deployment (force={force}, dry_run={dry_run})")
        
        # Validate configuration
        valid, config, error = await self.validate_config()
        if not valid:
            return False, error or "Configuration validation failed"
        
        if dry_run:
            return await self._dry_run_deployment(config)
        
        try:
            # Get platform instance
            platform = get_platform(config.platform, config.get_platform_config())
            
            # Validate credentials
            self.logger.info("Validating credentials")
            valid, message = await asyncio.to_thread(platform.validate_credentials)
            if not valid:
                return False, f"Credential validation failed: {message}"
            
            # Configure environment variables if platform supports it
            if hasattr(platform, 'set_environment_variables'):
                env_configurator = EnvConfigurator(str(self.project_path))
                
                if not force:  # Only ask if not forcing deployment
                    env_success, env_message = await asyncio.to_thread(
                        env_configurator.configure_environment_variables,
                        platform, config.platform
                    )
                    if not env_success:
                        self.logger.warning(f"Environment variable setup failed: {env_message}")
            
            # Prepare deployment
            self.logger.info("Preparing deployment")
            build_command = config.build.command
            output_dir = config.build.output
            
            prepared, prep_message = await asyncio.to_thread(
                platform.prepare_deployment,
                str(self.project_path),
                build_command,
                output_dir
            )
            
            if not prepared:
                return False, f"Preparation failed: {prep_message}"
            
            # Execute deployment
            self.logger.info("Executing deployment")
            result = await asyncio.to_thread(
                platform.execute_deployment,
                str(self.project_path),
                output_dir
            )
            
            if result.success:
                self.logger.info(f"Deployment successful: {result.url}")
                return True, f"Deployment successful: {result.url}"
            else:
                self.logger.error(f"Deployment failed: {result.message}")
                return False, f"Deployment failed: {result.message}"
                
        except Exception as e:
            error_msg = f"Deployment error: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    async def _dry_run_deployment(self, config: DeployXConfig) -> Tuple[bool, str]:
        """
        Simulate deployment without executing.
        
        Provides a preview of what would happen during deployment
        without actually performing any operations.
        
        Args:
            config: Validated configuration object
            
        Returns:
            Tuple containing success status and summary message
        """
        self.logger.info("Performing dry run")
        
        summary = [
            f"Platform: {config.platform}",
            f"Project: {config.project.name} ({config.project.type})",
            f"Build command: {config.build.command or 'None'}",
            f"Output directory: {config.build.output}"
        ]
        
        return True, "Dry run completed:\n" + "\n".join(f"  {item}" for item in summary)

class InitService:
    """
    Service for project initialization.
    
    Handles the setup of new DeployX projects by detecting project
    type, creating configuration files, and setting up default
    deployment settings.
    
    Attributes:
        project_path: Path to the project directory
        config: Configuration manager instance
        logger: Logger instance for this service
    """
    
    def __init__(self, project_path: str = "."):
        """
        Initialize project initialization service.
        
        Args:
            project_path: Path to project directory (default: current directory)
        """
        self.project_path = Path(project_path)
        self.config = Config(str(self.project_path))
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
    
    async def initialize_project(self) -> Tuple[bool, str]:
        """
        Initialize project configuration.
        
        Detects the project type, creates a default configuration,
        validates it using Pydantic models, and saves it to the
        configuration file.
        
        Returns:
            Tuple containing:
                - success: True if initialization succeeded
                - message: Success message or error description
        """
        self.logger.info("Starting project initialization")
        
        try:
            # Detect project type
            project_info = await asyncio.to_thread(detect_project, str(self.project_path))
            
            # Create basic configuration
            config_data = {
                "project": {
                    "name": self.project_path.name,
                    "type": project_info.type
                },
                "build": {
                    "command": project_info.build_command,
                    "output": project_info.output_dir
                },
                "platform": "github",  # Default platform
                "github": {
                    "repo": "username/repository",
                    "branch": "gh-pages",
                    "method": "branch"
                }
            }
            
            # Validate configuration
            validated_config = DeployXConfig(**config_data)
            
            # Save configuration
            self.config.save(validated_config.dict())
            
            self.logger.info("Project initialization completed")
            return True, "Project initialized successfully"
            
        except Exception as e:
            error_msg = f"Initialization failed: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

class StatusService:
    """
    Service for checking deployment status.
    
    Provides functionality to check the current status of deployments
    on various platforms, including build status, deployment URLs,
    and error information.
    
    Attributes:
        project_path: Path to the project directory
        config: Configuration manager instance
        logger: Logger instance for this service
    """
    
    def __init__(self, project_path: str = "."):
        """
        Initialize status checking service.
        
        Args:
            project_path: Path to project directory (default: current directory)
        """
        self.project_path = Path(project_path)
        self.config = Config(str(self.project_path))
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
    
    async def get_status(self) -> Tuple[bool, str]:
        """
        Get deployment status.
        
        Checks the current status of the deployment on the configured
        platform, including build status, live URL, and last update time.
        
        Returns:
            Tuple containing:
                - success: True if status check succeeded
                - message: Status information or error description
        """
        self.logger.info("Checking deployment status")
        
        try:
            # Validate configuration
            if not self.config.exists():
                return False, "No configuration found"
            
            config_data = self.config.load()
            validated_config = DeployXConfig(**config_data)
            
            # Get platform instance
            platform = get_platform(validated_config.platform, validated_config.get_platform_config())
            
            # Get status
            status = await asyncio.to_thread(platform.get_deployment_status)
            
            status_msg = f"Status: {status.status}"
            if status.url:
                status_msg += f"\nURL: {status.url}"
            if status.last_updated:
                status_msg += f"\nLast updated: {status.last_updated}"
            
            self.logger.info(f"Status check completed: {status.status}")
            return True, status_msg
            
        except Exception as e:
            error_msg = f"Status check failed: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
