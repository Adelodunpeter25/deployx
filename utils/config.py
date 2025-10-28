"""
Configuration management for DeployX.

This module handles loading, saving, and validating deployx.yml
configuration files. It provides a simple interface for accessing
project and platform-specific settings.

Example:
    >>> config = Config("./my-project")
    >>> if config.exists():
    ...     data = config.load()
    ...     platform = data.get('platform')
"""

import yaml
from pathlib import Path
from typing import Dict, Any

CONFIG_FILE = "deployx.yml"


class Config:
    """
    Configuration file manager for DeployX projects.
    
    Handles reading and writing deployx.yml files with caching
    to avoid repeated file I/O operations.
    
    Attributes:
        project_path: Path to the project directory
        config_path: Full path to deployx.yml file
        _data: Cached configuration data (empty dict if not loaded)
    
    Example:
        >>> config = Config("./my-project")
        >>> config.save({"platform": "github"})
        >>> data = config.load()
    """
    
    def __init__(self, project_path: str = "."):
        """
        Initialize configuration manager.
        
        Args:
            project_path: Path to project directory (default: current directory)
        """
        self.project_path = Path(project_path)
        self.config_path = self.project_path / CONFIG_FILE
        self._data = {}
    
    def load(self) -> Dict[str, Any]:
        """
        Load configuration from deployx.yml file.
        
        Caches the loaded data for subsequent access. Returns empty
        dict if file doesn't exist.
        
        Returns:
            Dict containing configuration data
        
        Raises:
            yaml.YAMLError: If configuration file is malformed
        """
        if not self.config_path.exists():
            return {}
        
        with open(self.config_path, 'r') as f:
            self._data = yaml.safe_load(f) or {}
        return self._data
    
    def save(self, data: Dict[str, Any]) -> None:
        """
        Save configuration to deployx.yml file.
        
        Writes data in YAML format with proper indentation.
        Updates internal cache.
        
        Args:
            data: Configuration dictionary to save
        
        Raises:
            IOError: If file cannot be written
        """
        self._data = data
        with open(self.config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, indent=2)
    
    def exists(self) -> bool:
        """
        Check if configuration file exists.
        
        Returns:
            True if deployx.yml exists, False otherwise
        """
        return self.config_path.exists()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Automatically loads configuration if not already loaded.
        
        Args:
            key: Configuration key to retrieve
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        if not self._data:
            self.load()
        return self._data.get(key, default)
    
    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        """
        Get platform-specific configuration section.
        
        Args:
            platform: Platform name (github, vercel, etc.)
        
        Returns:
            Platform configuration dict (empty if not found)
        """
        return self.get(platform, {})


def create_default_config(project_name: str, project_type: str, platform: str) -> Dict[str, Any]:
    """
    Create default configuration structure.
    
    Generates a basic configuration template with project info,
    build settings, and platform placeholder.
    
    Args:
        project_name: Name of the project
        project_type: Type of project (react, vue, static, etc.)
        platform: Target deployment platform
    
    Returns:
        Dict containing default configuration structure
    
    Example:
        >>> config = create_default_config("my-app", "react", "github")
        >>> config['project']['name']
        'my-app'
    """
    return {
        "project": {
            "name": project_name,
            "type": project_type
        },
        "build": {
            "command": "npm run build" if project_type == "react" else None,
            "output": "build" if project_type == "react" else "."
        },
        "platform": platform,
        platform: {}
    }
