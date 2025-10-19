"""
Configuration management commands for DeployX
"""

import os
import subprocess
from pathlib import Path
from utils.ui import header, success, error, info, warning, print_config_summary
from utils.config import Config
from utils.validator import validate_config

def config_show_command(project_path: str = ".") -> bool:
    """Show current configuration"""
    
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
    """Edit configuration file"""
    
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
    """Validate configuration without deploying"""
    
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