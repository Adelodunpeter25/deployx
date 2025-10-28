"""
Configuration management commands for DeployX.

Provides commands to view, edit, and validate deployx.yml configuration files.
Helps users manage their deployment settings without manual file editing.

Example:
    >>> from commands.config import config_show_command
    >>> config_show_command("./my-project")
"""

import os
import subprocess
from pathlib import Path
from utils.ui import header, success, error, info, print_config_summary
from utils.config import Config
from utils.validator import validate_config


def config_show_command(project_path: str = ".") -> bool:
    """
    Show current configuration.
    
    Displays the contents of deployx.yml in a formatted view
    with project, build, and platform settings.
    
    Args:
        project_path: Path to project directory (default: current directory)
    
    Returns:
        True if successful, False otherwise
    
    Example:
        >>> config_show_command("./my-app")
        True
    """
    config = Config(project_path)
    
    if not config.exists():
        error("❌ No configuration found. Run 'deployx init' first.")
        return False
    
    try:
        config_data = config.load()
        
        header("DeployX Configuration")
        print_config_summary(config_data)
        
        # Show config file path
        config_file = Path(project_path) / "deployx.yml"
        info(f"📄 Configuration file: {config_file.absolute()}")
        
        return True
        
    except Exception as e:
        error(f"❌ Failed to load configuration: {str(e)}")
        return False


def config_edit_command(project_path: str = ".") -> bool:
    """
    Edit configuration file.
    
    Opens deployx.yml in the system's default editor (from EDITOR env var).
    Automatically validates configuration after editing.
    
    Args:
        project_path: Path to project directory (default: current directory)
    
    Returns:
        True if edit and validation successful, False otherwise
    
    Note:
        Uses $EDITOR environment variable, defaults to 'nano' if not set.
    
    Example:
        >>> config_edit_command("./my-app")
        True
    """
    config = Config(project_path)
    config_file = Path(project_path) / "deployx.yml"
    
    if not config.exists():
        error("❌ No configuration found. Run 'deployx init' first.")
        return False
    
    try:
        # Try to open with system editor
        editor = os.getenv('EDITOR', 'nano')  # Default to nano
        
        info(f"📝 Opening configuration with {editor}...")
        
        result = subprocess.run([editor, str(config_file)])
        
        if result.returncode == 0:
            success("✅ Configuration file updated")
            
            # Validate after editing
            info("🔍 Validating configuration...")
            return config_validate_command(project_path)
        else:
            error("❌ Editor exited with error")
            return False
            
    except FileNotFoundError:
        error(f"❌ Editor '{editor}' not found. Set EDITOR environment variable.")
        info("💡 Try: export EDITOR=nano  # or vim, code, etc.")
        return False
    except Exception as e:
        error(f"❌ Failed to edit configuration: {str(e)}")
        return False


def config_validate_command(project_path: str = ".") -> bool:
    """
    Validate configuration without deploying.
    
    Checks deployx.yml for required fields, valid platform names,
    and supported project types. Useful before deployment.
    
    Args:
        project_path: Path to project directory (default: current directory)
    
    Returns:
        True if configuration is valid, False otherwise
    
    Example:
        >>> config_validate_command("./my-app")
        True
    """
    config = Config(project_path)
    
    if not config.exists():
        error("❌ No configuration found. Run 'deployx init' first.")
        return False
    
    try:
        config_data = config.load()
        
        info("🔍 Validating configuration...")
        
        # Run validation
        errors = validate_config(config_data)
        
        if errors:
            error("❌ Configuration validation failed:")
            for err in errors:
                print(f"  • {err}")
            return False
        else:
            success("✅ Configuration is valid")
            
            # Show summary
            print_config_summary(config_data)
            return True
            
    except Exception as e:
        error(f"❌ Failed to validate configuration: {str(e)}")
        return False
