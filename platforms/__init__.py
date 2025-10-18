# Import and register all platforms
from .factory import PlatformFactory
from .github import GitHubPlatform

# Register platforms
PlatformFactory.register_platform('github', GitHubPlatform)