"""
Vercel CLI integration for authentication and project management.
"""
import subprocess
import json
import os
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from core.logging import get_logger

class VercelCLIIntegration:
    """Integration with Vercel CLI for authentication and operations."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def is_cli_available(self) -> bool:
        """Check if Vercel CLI is installed and authenticated."""
        try:
            result = subprocess.run(
                ["vercel", "whoami"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def get_authenticated_user(self) -> Optional[str]:
        """Get the authenticated Vercel username."""
        try:
            result = subprocess.run(
                ["vercel", "whoami"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Failed to get authenticated user: {e}")
        return None
    
    def get_token(self) -> Optional[str]:
        """Get Vercel token from CLI config."""
        try:
            # Try to get token from Vercel CLI config
            config_path = Path.home() / '.vercel' / 'auth.json'
            if config_path.exists():
                with open(config_path, 'r') as f:
                    auth_data = json.load(f)
                    return auth_data.get('token')
        except Exception as e:
            self.logger.error(f"Failed to get token: {str(e)}")
        return None
    
    def create_project(self, project_name: str, project_path: str = ".") -> Tuple[bool, str]:
        """Create a Vercel project using CLI."""
        try:
            result = subprocess.run(
                ["vercel", "--yes", "--name", project_name],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info(f"Created Vercel project: {project_name}")
                return True, f"Successfully created project: {project_name}"
            else:
                return False, f"Failed to create project: {result.stderr}"
                
        except Exception as e:
            return False, f"Failed to create project: {str(e)}"
    
    def deploy_project(self, project_path: str = ".") -> Tuple[bool, str, Optional[str]]:
        """Deploy project using Vercel CLI."""
        try:
            result = subprocess.run(
                ["vercel", "--prod", "--yes"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Extract URL from output
                lines = result.stdout.strip().split('\n')
                url = None
                for line in lines:
                    if 'https://' in line and 'vercel.app' in line:
                        url = line.strip()
                        break
                
                return True, "Deployment successful", url
            else:
                return False, f"Deployment failed: {result.stderr}", None
                
        except Exception as e:
            return False, f"Deployment failed: {str(e)}", None
    
    def get_project_info(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get project information."""
        try:
            result = subprocess.run(
                ["vercel", "ls", project_name, "--json"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception as e:
            self.logger.error(f"Failed to get project info: {e}")
        return None
