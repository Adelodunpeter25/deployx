"""
Railway CLI integration for authentication and operations.
"""
import subprocess
import json
import os
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from core.logging import get_logger

class RailwayCLIIntegration:
    """Integration with Railway CLI for authentication and operations."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def is_cli_available(self) -> bool:
        """Check if Railway CLI is installed and authenticated."""
        try:
            result = subprocess.run(
                ["railway", "whoami"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def get_authenticated_user(self) -> Optional[str]:
        """Get the authenticated Railway username."""
        try:
            result = subprocess.run(
                ["railway", "whoami"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Failed to get authenticated user: {e}")
        return None
    
    def get_token(self) -> Optional[str]:
        """Get Railway token from CLI config."""
        try:
            # Try to get token from Railway CLI config
            config_path = Path.home() / '.railway' / 'config.json'
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    return config_data.get('token')
        except Exception as e:
            self.logger.error(f"Failed to get token: {str(e)}")
        return None
    
    def login(self) -> Tuple[bool, str]:
        """Login using Railway CLI."""
        try:
            result = subprocess.run(
                ["railway", "login"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, "Successfully logged in to Railway"
            else:
                return False, f"Login failed: {result.stderr}"
                
        except Exception as e:
            return False, f"Login error: {str(e)}"
    
    def create_project(self, project_name: str, project_path: str = ".") -> Tuple[bool, str]:
        """Create a Railway project using CLI."""
        try:
            result = subprocess.run(
                ["railway", "new", project_name],
                cwd=project_path,
                capture_output=True,
                text=True,
                input="y\n"  # Confirm project creation
            )
            
            if result.returncode == 0:
                self.logger.info(f"Created Railway project: {project_name}")
                return True, f"Successfully created project: {project_name}"
            else:
                return False, f"Failed to create project: {result.stderr}"
                
        except Exception as e:
            return False, f"Failed to create project: {str(e)}"
    
    def link_project(self, project_id: str, project_path: str = ".") -> Tuple[bool, str]:
        """Link current directory to a Railway project."""
        try:
            result = subprocess.run(
                ["railway", "link", project_id],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, f"Successfully linked to project: {project_id}"
            else:
                return False, f"Failed to link project: {result.stderr}"
                
        except Exception as e:
            return False, f"Link error: {str(e)}"
    
    def deploy_project(self, project_path: str = ".") -> Tuple[bool, str, Optional[str]]:
        """Deploy project using Railway CLI."""
        try:
            result = subprocess.run(
                ["railway", "up"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Extract URL from output if available
                lines = result.stdout.strip().split('\n')
                url = None
                for line in lines:
                    if 'https://' in line and 'railway.app' in line:
                        url = line.strip()
                        break
                
                return True, "Deployment successful", url
            else:
                return False, f"Deployment failed: {result.stderr}", None
                
        except Exception as e:
            return False, f"Deployment failed: {str(e)}", None
    
    def get_project_info(self, project_path: str = ".") -> Optional[Dict[str, Any]]:
        """Get current project information."""
        try:
            result = subprocess.run(
                ["railway", "status"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                # Parse status output (Railway CLI doesn't provide JSON output)
                return {"status": result.stdout.strip()}
        except Exception as e:
            self.logger.error(f"Failed to get project info: {e}")
        return None
    
    def set_environment_variable(self, key: str, value: str, project_path: str = ".") -> Tuple[bool, str]:
        """Set an environment variable."""
        try:
            result = subprocess.run(
                ["railway", "variables", "set", f"{key}={value}"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, f"Set environment variable: {key}"
            else:
                return False, f"Failed to set variable: {result.stderr}"
                
        except Exception as e:
            return False, f"Variable error: {str(e)}"
