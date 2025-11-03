"""
Platform factory for creating deployment platform instances.

Uses factory pattern to create appropriate platform objects based
on platform name. Maintains registry of available platforms.
"""

from typing import Dict, Any, Optional
from .base import BasePlatform
from .github import GitHubPlatform
from .vercel import VercelPlatform
from .netlify import NetlifyPlatform
from .railway import RailwayPlatform
from .render import RenderPlatform


class PlatformFactory:
    """
    Factory for creating platform instances.
    
    Maintains a registry of available platforms and creates
    instances on demand. Supports dynamic platform registration.
    
    Class Attributes:
        _platforms: Dict mapping platform names to platform classes
    """
    
    _platforms = {}
    
    @classmethod
    def register_platform(cls, name: str, platform_class):
        """
        Register a platform class.
        
        Adds platform to the registry so it can be created by name.
        
        Args:
            name: Platform name (e.g., "github", "vercel")
            platform_class: Platform class (must inherit from BasePlatform)
        """
        cls._platforms[name] = platform_class
    
    @classmethod
    def create_platform(cls, platform_name: str, config: Dict[str, Any]) -> Optional[BasePlatform]:
        """
        Create platform instance by name.
        
        Args:
            platform_name: Name of platform to create
            config: Platform-specific configuration
        
        Returns:
            Platform instance
        
        Raises:
            ValueError: If platform name is not registered
        """
        if platform_name not in cls._platforms:
            raise ValueError(
                f"Unknown platform: {platform_name}. "
                f"Available: {list(cls._platforms.keys())}"
            )
        
        platform_class = cls._platforms[platform_name]
        return platform_class(config)
    
    @classmethod
    def get_available_platforms(cls) -> list:
        """
        Get list of available platform names.
        
        Returns:
            List of registered platform names
        """
        return list(cls._platforms.keys())


def get_platform(platform_name: str, config: Dict[str, Any]) -> BasePlatform:
    """
    Convenience function to get platform instance.
    
    Wrapper around PlatformFactory.create_platform for easier imports.
    
    Args:
        platform_name: Name of platform to create
        config: Platform-specific configuration
    
    Returns:
        Platform instance
    
    Raises:
        ValueError: If platform name is not registered
    """
    return PlatformFactory.create_platform(platform_name, config)


# Register all available platforms
PlatformFactory.register_platform("github", GitHubPlatform)
PlatformFactory.register_platform("vercel", VercelPlatform)
PlatformFactory.register_platform("netlify", NetlifyPlatform)
PlatformFactory.register_platform("railway", RailwayPlatform)
PlatformFactory.register_platform("render", RenderPlatform)
