from typing import Dict, Any, Optional
from .base import BasePlatform
from .github import GitHubPlatform
from .vercel import VercelPlatform
from .netlify import NetlifyPlatform
from .railway import RailwayPlatform
from .render import RenderPlatform

class PlatformFactory:
    """Factory for creating platform instances"""
    
    _platforms = {}
    
    @classmethod
    def register_platform(cls, name: str, platform_class):
        """Register a platform class"""
        cls._platforms[name] = platform_class
    
    @classmethod
    def create_platform(cls, platform_name: str, config: Dict[str, Any]) -> Optional[BasePlatform]:
        """Create platform instance"""
        if platform_name not in cls._platforms:
            raise ValueError(f"Unknown platform: {platform_name}. Available: {list(cls._platforms.keys())}")
        
        platform_class = cls._platforms[platform_name]
        return platform_class(config)
    
    @classmethod
    def get_available_platforms(cls) -> list:
        """Get list of available platforms"""
        return list(cls._platforms.keys())

def get_platform(platform_name: str, config: Dict[str, Any]) -> BasePlatform:
    """Convenience function to get platform instance"""
    return PlatformFactory.create_platform(platform_name, config)

# Register all platforms
PlatformFactory.register_platform("github", GitHubPlatform)
PlatformFactory.register_platform("vercel", VercelPlatform)
PlatformFactory.register_platform("netlify", NetlifyPlatform)
PlatformFactory.register_platform("railway", RailwayPlatform)
PlatformFactory.register_platform("render", RenderPlatform)