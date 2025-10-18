from typing import Dict, Any, List

REQUIRED_FIELDS = {
    "project": ["name", "type"],
    "build": ["output"],
    "platform": []
}

SUPPORTED_PLATFORMS = ["github", "vercel", "netlify", "railway", "render"]
SUPPORTED_PROJECT_TYPES = ["react", "vue", "static", "nextjs", "python", "django", "flask", "fastapi", "nodejs", "angular", "vite"]

def validate_config(config: Dict[str, Any]) -> List[str]:
    """Validate configuration and return list of errors"""
    errors = []
    
    # Check required top-level fields
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
            errors.append(f"Unsupported platform: {platform}. Supported: {SUPPORTED_PLATFORMS}")
        
        # Check platform-specific config exists
        if platform not in config:
            errors.append(f"Missing configuration for platform: {platform}")
    
    # Validate project type
    if "project" in config and "type" in config["project"]:
        project_type = config["project"]["type"]
        if project_type not in SUPPORTED_PROJECT_TYPES:
            errors.append(f"Unsupported project type: {project_type}. Supported: {SUPPORTED_PROJECT_TYPES}")
    
    return errors