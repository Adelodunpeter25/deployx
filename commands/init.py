"""
Initialization command for DeployX.

Handles project detection, platform selection, and configuration
file creation. Guides users through interactive setup process.

This module orchestrates the initialization workflow by:
1. Detecting project type and framework
2. Prompting for platform selection
3. Collecting platform-specific settings
4. Validating and saving configuration

Example:
    >>> from commands.init import init_command
    >>> success = init_command("./my-project")
    >>> if success:
    ...     print("Configuration created successfully")
"""

import questionary

from utils.ui import header, success, error, info, warning, print_config_summary, platform_selection_wizard
from utils.config import Config, create_default_config
from utils.validator import validate_config
from detectors.project import detect_project, get_project_summary

# Import extracted helper modules
from commands.init_utils import (
    detect_git_repository,
    get_project_name,
    configure_build_settings,
    display_detection_results,
    show_next_steps
)
from commands.platform_config import (
    configure_github,
    configure_vercel,
    configure_netlify,
    configure_railway,
    configure_render
)


def init_command(project_path: str = ".", skip_header: bool = False) -> bool:
    """
    Initialize DeployX configuration for a project.
    
    Runs interactive setup wizard that detects project type,
    prompts for platform selection, collects necessary credentials,
    and creates deployx.yml configuration file.
    
    Args:
        project_path: Path to project directory (default: current directory)
        skip_header: Skip displaying welcome header (default: False)
    
    Returns:
        True if initialization successful, False otherwise
    
    Example:
        >>> init_command("./my-react-app")
        True
    """
    # Display welcome message
    if not skip_header:
        header("Initialize Configuration")
        print("🚀 One CLI for all your deployments, stop memorizing platform-specific commands\n")
    
    config = Config(project_path)
    
    # Check if configuration already exists
    if not _handle_existing_config(config):
        return False
    
    # Run project detection and display results
    project_info = detect_project(project_path)
    summary = get_project_summary(project_info)
    display_detection_results(summary)
    
    # Platform selection with visual wizard
    platform = platform_selection_wizard()
    if not platform:
        error("Platform selection cancelled")
        return False
    
    # Get platform-specific configuration
    platform_config = _get_platform_configuration(platform, project_path, summary)
    if platform_config is None:
        return False
    
    # Configure build settings
    build_config = configure_build_settings(summary)
    
    # Create and save configuration
    return _create_and_save_config(
        config,
        project_path,
        summary,
        platform,
        platform_config,
        build_config
    )


def _handle_existing_config(config: Config) -> bool:
    """
    Handle case where configuration already exists.
    
    Prompts user to confirm overwrite if config file exists.
    
    Args:
        config: Config object for the project
    
    Returns:
        True to continue, False to cancel
    """
    if config.exists():
        warning("Configuration file already exists")
        overwrite = questionary.confirm(
            "Do you want to overwrite the existing configuration?",
            default=False
        ).ask()
        
        if not overwrite:
            info("Setup cancelled. Use 'deployx deploy' to deploy with existing config.")
            return False
    
    return True


def _get_platform_configuration(platform: str, project_path: str, 
                                summary: dict) -> dict:
    """
    Get platform-specific configuration.
    
    Routes to appropriate platform configuration function based
    on selected platform.
    
    Args:
        platform: Selected platform name
        project_path: Path to project directory
        summary: Project detection summary
    
    Returns:
        Platform configuration dict or None if cancelled
    """
    # Map platforms to their configuration functions
    platform_handlers = {
        "github": lambda: configure_github(
            project_path, summary, detect_git_repository, get_project_name
        ),
        "vercel": lambda: configure_vercel(
            project_path, summary, get_project_name
        ),
        "netlify": lambda: configure_netlify(
            project_path, summary, get_project_name
        ),
        "railway": lambda: configure_railway(
            project_path, summary, get_project_name
        ),
        "render": lambda: configure_render(
            project_path, summary, get_project_name
        )
    }
    
    # Get handler for selected platform
    handler = platform_handlers.get(platform)
    if not handler:
        error(f"Unknown platform: {platform}")
        return None
    
    # Execute platform configuration
    return handler()


def _create_and_save_config(config: Config, project_path: str, summary: dict,
                            platform: str, platform_config: dict, 
                            build_config: dict) -> bool:
    """
    Create configuration structure and save to file.
    
    Validates configuration before saving and displays summary.
    
    Args:
        config: Config object for saving
        project_path: Path to project directory
        summary: Project detection summary
        platform: Selected platform name
        platform_config: Platform-specific configuration
        build_config: Build settings configuration
    
    Returns:
        True if successful, False otherwise
    """
    # Create configuration structure
    config_data = create_default_config(
        get_project_name(project_path, summary),
        summary['type'],
        platform
    )
    
    # Update with user inputs
    config_data['build'] = build_config
    config_data[platform] = platform_config
    
    # Validate configuration
    errors = validate_config(config_data)
    if errors:
        error("Configuration validation failed:")
        for err in errors:
            print(f"  • {err}")
        return False
    
    # Save configuration
    try:
        config.save(config_data)
        success("✅ Configuration saved to deployx.yml")
        
        # Display summary
        print_config_summary(config_data)
        
        # Show next steps
        show_next_steps()
        
        return True
        
    except Exception as e:
        error(f"Failed to save configuration: {str(e)}")
        return False
