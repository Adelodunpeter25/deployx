"""
Environment variable interface for deployment platforms.

Defines the interface for setting environment variables on different platforms
and provides base functionality for environment variable management.
"""
from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional
from core.logging import get_logger

class PlatformEnvInterface(ABC):
    """Abstract interface for platform environment variable management."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    @abstractmethod
    def set_environment_variables(self, env_vars: Dict[str, str]) -> Tuple[bool, str]:
        """
        Set environment variables on the platform.
        
        Args:
            env_vars: Dictionary of environment variables to set
            
        Returns:
            Tuple of (success, message)
        """
        pass
    
    @abstractmethod
    def get_environment_variables(self) -> Tuple[bool, Dict[str, str], str]:
        """
        Get existing environment variables from the platform.
        
        Returns:
            Tuple of (success, env_vars, error_message)
        """
        pass
    
    @abstractmethod
    def delete_environment_variable(self, key: str) -> Tuple[bool, str]:
        """
        Delete an environment variable from the platform.
        
        Args:
            key: Environment variable key to delete
            
        Returns:
            Tuple of (success, message)
        """
        pass
    
    def update_environment_variables(self, env_vars: Dict[str, str], 
                                   overwrite: bool = True) -> Tuple[bool, str]:
        """
        Update environment variables, handling conflicts.
        
        Args:
            env_vars: New environment variables to set
            overwrite: Whether to overwrite existing variables
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get existing variables
            success, existing_vars, error = self.get_environment_variables()
            if not success:
                self.logger.warning(f"Could not fetch existing variables: {error}")
                existing_vars = {}
            
            # Check for conflicts
            conflicts = set(env_vars.keys()) & set(existing_vars.keys())
            
            if conflicts and not overwrite:
                conflict_list = ", ".join(conflicts)
                return False, f"Variables already exist: {conflict_list}. Use overwrite=True to replace."
            
            # Set the variables
            return self.set_environment_variables(env_vars)
            
        except Exception as e:
            error_msg = f"Failed to update environment variables: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def validate_environment_variables(self, env_vars: Dict[str, str]) -> Tuple[bool, str]:
        """
        Validate environment variables before setting.
        
        Args:
            env_vars: Environment variables to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not env_vars:
            return False, "No environment variables provided"
        
        # Check for empty keys
        empty_keys = [key for key, value in env_vars.items() if not key.strip()]
        if empty_keys:
            return False, "Environment variable keys cannot be empty"
        
        # Check for invalid characters in keys (platform-specific validation can override)
        invalid_keys = []
        for key in env_vars.keys():
            if not key.replace('_', '').replace('-', '').isalnum():
                invalid_keys.append(key)
        
        if invalid_keys:
            return False, f"Invalid characters in keys: {', '.join(invalid_keys)}"
        
        return True, ""
    
    def format_env_vars_summary(self, env_vars: Dict[str, str]) -> str:
        """
        Create a summary of environment variables for display.
        
        Args:
            env_vars: Environment variables to summarize
            
        Returns:
            Formatted summary string
        """
        if not env_vars:
            return "No environment variables"
        
        summary_lines = []
        for key, value in env_vars.items():
            # Show preview of value
            if len(value) > 20:
                preview = f"{value[:17]}..."
            else:
                preview = value
            
            summary_lines.append(f"  {key}={preview}")
        
        return f"{len(env_vars)} variables:\n" + "\n".join(summary_lines)
