"""
Environment variable configuration for deployment platforms.

Handles the integration of environment variables during project initialization
and deployment processes.
"""
from typing import Tuple
import questionary
from utils.env_manager import EnvManager
from utils.ui import info, success, warning, error
from platforms.env_interface import PlatformEnvInterface
from core.logging import get_logger

class EnvConfigurator:
    """Handles environment variable configuration for platforms."""
    
    def __init__(self, project_path: str = "."):
        self.project_path = project_path
        self.env_manager = EnvManager(project_path)
        self.logger = get_logger(__name__)
    
    def configure_environment_variables(self, platform: PlatformEnvInterface, 
                                      platform_name: str) -> Tuple[bool, str]:
        """
        Configure environment variables for a platform.
        
        Args:
            platform: Platform instance that supports environment variables
            platform_name: Name of the platform for display
            
        Returns:
            Tuple of (success, message)
        """
        try:
            info(f"🌍 Environment Variable Setup for {platform_name.title()}")
            
            # Check if user wants to configure environment variables
            if not questionary.confirm(
                f"Configure environment variables for {platform_name}?",
                default=False
            ).ask():
                return True, "Environment variable configuration skipped"
            
            # Collect environment variables
            env_vars = self.env_manager.collect_env_variables()
            
            if not env_vars:
                info("No environment variables configured")
                return True, "No environment variables to configure"
            
            # Show summary and confirm
            summary = platform.format_env_vars_summary(env_vars)
            info(f"📋 Environment variables to configure:\n{summary}")
            
            if not questionary.confirm(
                f"Set these {len(env_vars)} variables on {platform_name}?",
                default=True
            ).ask():
                return True, "Environment variable configuration cancelled"
            
            # Set the variables on the platform
            success_result, message = platform.set_environment_variables(env_vars)
            
            if success_result:
                success(f"✅ {message}")
                self.logger.info(f"Environment variables configured for {platform_name}")
                return True, message
            else:
                error(f"❌ {message}")
                return False, message
                
        except Exception as e:
            error_msg = f"Environment variable configuration failed: {str(e)}"
            self.logger.error(error_msg)
            error(f"❌ {error_msg}")
            return False, error_msg
    
    def update_environment_variables(self, platform: PlatformEnvInterface,
                                   platform_name: str) -> Tuple[bool, str]:
        """
        Update existing environment variables on a platform.
        
        Args:
            platform: Platform instance that supports environment variables
            platform_name: Name of the platform for display
            
        Returns:
            Tuple of (success, message)
        """
        try:
            info(f"🔄 Update Environment Variables for {platform_name.title()}")
            
            # Get existing variables
            success_result, existing_vars, error_msg = platform.get_environment_variables()
            if not success_result:
                warning(f"Could not fetch existing variables: {error_msg}")
                existing_vars = {}
            
            if existing_vars:
                info(f"📋 Current variables: {', '.join(existing_vars.keys())}")
            
            # Collect new variables
            env_vars = self.env_manager.collect_env_variables()
            
            if not env_vars:
                return True, "No new environment variables to configure"
            
            # Check for conflicts
            conflicts = set(env_vars.keys()) & set(existing_vars.keys())
            if conflicts:
                conflict_list = ", ".join(conflicts)
                warning(f"⚠️  Variables already exist: {conflict_list}")
                
                overwrite = questionary.confirm(
                    "Overwrite existing variables?",
                    default=False
                ).ask()
                
                if not overwrite:
                    return True, "Update cancelled to avoid overwriting existing variables"
            
            # Update the variables
            return platform.update_environment_variables(env_vars, overwrite=True)
            
        except Exception as e:
            error_msg = f"Environment variable update failed: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def show_environment_variables(self, platform: PlatformEnvInterface,
                                 platform_name: str) -> Tuple[bool, str]:
        """
        Show current environment variables on a platform.
        
        Args:
            platform: Platform instance that supports environment variables
            platform_name: Name of the platform for display
            
        Returns:
            Tuple of (success, message)
        """
        try:
            success_result, env_vars, error_msg = platform.get_environment_variables()
            
            if not success_result:
                return False, f"Failed to get environment variables: {error_msg}"
            
            if not env_vars:
                info(f"📋 No environment variables configured on {platform_name}")
                return True, "No environment variables found"
            
            info(f"📋 Environment variables on {platform_name.title()}:")
            for key, value in env_vars.items():
                # Show preview for security
                if len(value) > 20:
                    preview = f"{value[:17]}..."
                else:
                    preview = value
                print(f"  {key}={preview}")
            
            return True, f"Found {len(env_vars)} environment variables"
            
        except Exception as e:
            error_msg = f"Failed to show environment variables: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
