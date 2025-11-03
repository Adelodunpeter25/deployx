"""
Configuration validation for DeployX.

Validates deployx.yml configuration files to ensure all required
fields are present and values are valid before deployment.

Example:
    >>> config = {"project": {"name": "app", "type": "react"}}
    >>> errors = validate_config(config)
    >>> if errors:
    ...     print("Invalid configuration")
"""

from typing import Dict, Any, List

try:
    from core.constants import SUPPORTED_PLATFORMS, SUPPORTED_PROJECT_TYPES
except ImportError:
    # Fallback if constants not available
    SUPPORTED_PLATFORMS = ["github", "vercel", "netlify", "railway", "render"]
    SUPPORTED_PROJECT_TYPES = [
        "react", "vue", "static", "nextjs", "python", 
        "django", "flask", "fastapi", "nodejs", "angular", "vite"
    ]

# Required fields for each configuration section
REQUIRED_FIELDS = {
    "project": ["name", "type"],
    "build": ["output"],
    "platform": []
}


def validate_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate configuration and return list of errors.
    
    Checks for required fields, valid platform names, and
    supported project types. Returns empty list if valid.
    
    Args:
        config: Configuration dictionary to validate
    
    Returns:
        List of error messages (empty if valid)
    
    Example:
        >>> config = {"project": {"name": "app"}}
        >>> errors = validate_config(config)
        >>> errors
        ['Missing required field: project.type', ...]
    """
    errors = []
    
    # Check required top-level sections
    for section in ["project", "build", "platform"]:
        if section not in config:
            errors.append(f"Missing required section: {section}")
            continue
            
        # Check required fields in each section
        if section in REQUIRED_FIELDS:
            for field in REQUIRED_FIELDS[section]:
                if field not in config[section]:
                    errors.append(f"Missing required field: {section}.{field}")
    
    # Validate platform
    if "platform" in config:
        platform = config["platform"]
        if platform not in SUPPORTED_PLATFORMS:
            errors.append(
                f"Unsupported platform: {platform}. "
                f"Supported: {', '.join(SUPPORTED_PLATFORMS)}"
            )
        
        # Check platform-specific config exists
        if platform not in config:
            errors.append(f"Missing configuration for platform: {platform}")
    
    # Validate project type
    if "project" in config and "type" in config["project"]:
        project_type = config["project"]["type"]
        if project_type not in SUPPORTED_PROJECT_TYPES:
            errors.append(
                f"Unsupported project type: {project_type}. "
                f"Supported: {', '.join(SUPPORTED_PROJECT_TYPES)}"
            )
    
    return errors
