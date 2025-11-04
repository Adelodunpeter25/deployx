"""
GitHub CLI integration for authentication and repository management.
"""
import subprocess
import json
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from core.logging import get_logger

class GitHubCLIIntegration:
    """Integration with GitHub CLI (gh) for authentication and operations."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def is_cli_available(self) -> bool:
        """Check if GitHub CLI is installed and authenticated."""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def get_authenticated_user(self) -> Optional[str]:
        """Get the authenticated GitHub username."""
        try:
            result = subprocess.run(
                ["gh", "api", "user"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                user_data = json.loads(result.stdout)
                return user_data.get("login")
        except Exception as e:
            self.logger.error(f"Failed to get authenticated user: {e}")
        return None
    
    def get_token(self) -> Optional[str]:
        """Get GitHub token from CLI."""
        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Failed to get token: {str(e)}")
        return None
    
    def create_repository(self, repo_name: str, is_private: bool = False) -> Tuple[bool, str]:
        """Create a GitHub repository using CLI."""
        try:
            cmd = ["gh", "repo", "create", repo_name]
            if not is_private:
                cmd.append("--public")
            else:
                cmd.append("--private")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, f"Repository {repo_name} created successfully"
            else:
                return False, result.stderr.strip()
                
        except Exception as e:
            return False, f"Failed to create repository: {str(e)}"
    
    def enable_github_pages(self, repo_name: str, branch: str = "gh-pages") -> Tuple[bool, str]:
        """Enable GitHub Pages for a repository."""
        try:
            # Enable GitHub Pages via API call through gh CLI
            api_data = {
                "source": {
                    "branch": branch,
                    "path": "/"
                }
            }
            
            result = subprocess.run([
                "gh", "api", f"repos/{repo_name}/pages",
                "--method", "POST",
                "--input", "-"
            ], input=json.dumps(api_data), text=True, capture_output=True)
            
            if result.returncode == 0:
                return True, f"GitHub Pages enabled for {repo_name}"
            else:
                # Pages might already be enabled
                if "already exists" in result.stderr:
                    return True, f"GitHub Pages already enabled for {repo_name}"
                return False, result.stderr.strip()
                
        except Exception as e:
            return False, f"Failed to enable GitHub Pages: {str(e)}"
    
    def get_repository_info(self, repo_name: str) -> Optional[Dict[str, Any]]:
        """Get repository information."""
        try:
            result = subprocess.run([
                "gh", "api", f"repos/{repo_name}"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception as e:
            self.logger.error(f"Failed to get repository info: {e}")
        return None
