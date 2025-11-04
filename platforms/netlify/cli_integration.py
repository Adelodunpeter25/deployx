"""
Netlify CLI integration for authentication and operations.
"""
import subprocess
import json
import os
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from core.logging import get_logger

class NetlifyCLIIntegration:
    """Integration with Netlify CLI for authentication and operations."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def is_cli_available(self) -> bool:
        """Check if Netlify CLI is installed and authenticated."""
        try:
            result = subprocess.run(
                ["netlify", "status"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0 and "Logged in" in result.stdout
        except FileNotFoundError:
            return False
    
    def get_authenticated_user(self) -> Optional[str]:
        """Get the authenticated Netlify username."""
        try:
            result = subprocess.run(
                ["netlify", "status"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                # Parse status output to extract user info
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Email:' in line:
                        return line.split('Email:')[1].strip()
        except Exception as e:
            self.logger.error(f"Failed to get authenticated user: {e}")
        return None
    
    def get_token(self) -> Optional[str]:
        """Get Netlify token from CLI config."""
        try:
            # Try to get token from Netlify CLI config
            config_path = Path.home() / '.netlify' / 'config.json'
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    return config_data.get('accessToken')
        except Exception as e:
            self.logger.error(f"Failed to get token: {str(e)}")
        return None
    
    def create_site(self, site_name: str, project_path: str = ".") -> Tuple[bool, str, Optional[str]]:
        """Create a Netlify site using CLI."""
        try:
            result = subprocess.run(
                ["netlify", "sites:create", "--name", site_name],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Extract site ID from output
                lines = result.stdout.split('\n')
                site_id = None
                for line in lines:
                    if 'Site ID:' in line:
                        site_id = line.split('Site ID:')[1].strip()
                        break
                
                self.logger.info(f"Created Netlify site: {site_name}")
                return True, f"Successfully created site: {site_name}", site_id
            else:
                return False, f"Failed to create site: {result.stderr}", None
                
        except Exception as e:
            return False, f"Failed to create site: {str(e)}", None
    
    def deploy_site(self, project_path: str = ".", build_dir: str = "build") -> Tuple[bool, str, Optional[str]]:
        """Deploy site using Netlify CLI."""
        try:
            result = subprocess.run(
                ["netlify", "deploy", "--prod", "--dir", build_dir],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Extract URL from output
                lines = result.stdout.split('\n')
                url = None
                for line in lines:
                    if 'Website URL:' in line:
                        url = line.split('Website URL:')[1].strip()
                        break
                    elif 'https://' in line and 'netlify.app' in line:
                        url = line.strip()
                        break
                
                return True, "Deployment successful", url
            else:
                return False, f"Deployment failed: {result.stderr}", None
                
        except Exception as e:
            return False, f"Deployment failed: {str(e)}", None
    
    def get_site_info(self, project_path: str = ".") -> Optional[Dict[str, Any]]:
        """Get current site information."""
        try:
            result = subprocess.run(
                ["netlify", "status"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                # Parse status output
                return {"status": result.stdout.strip()}
        except Exception as e:
            self.logger.error(f"Failed to get site info: {e}")
        return None
    
    def link_site(self, site_id: str, project_path: str = ".") -> Tuple[bool, str]:
        """Link current directory to a Netlify site."""
        try:
            result = subprocess.run(
                ["netlify", "link", "--id", site_id],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, f"Successfully linked to site: {site_id}"
            else:
                return False, f"Failed to link site: {result.stderr}"
                
        except Exception as e:
            return False, f"Link error: {str(e)}"
