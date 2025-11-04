"""
Git utilities for repository detection and management.
"""
import subprocess
from typing import Optional, Tuple
from pathlib import Path
from core.logging import get_logger

class GitUtils:
    """Utilities for Git repository operations."""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.logger = get_logger(__name__)
    
    def is_git_repository(self) -> bool:
        """Check if current directory is a Git repository."""
        try:
            result = subprocess.run(
                ["git", "status"],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def has_remote_origin(self) -> bool:
        """Check if repository has a remote origin."""
        try:
            result = subprocess.run(
                ["git", "remote", "-v"],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0 and "origin" in result.stdout
        except Exception:
            return False
    
    def get_remote_origin_url(self) -> Optional[str]:
        """Get the remote origin URL."""
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Failed to get remote origin URL: {e}")
        return None
    
    def extract_repo_name_from_url(self, url: str) -> Optional[str]:
        """Extract repository name from Git URL."""
        try:
            # Handle both SSH and HTTPS URLs
            if url.startswith("git@github.com:"):
                # SSH: git@github.com:user/repo.git
                repo_part = url.split(":")[-1]
            elif "github.com/" in url:
                # HTTPS: https://github.com/user/repo.git
                repo_part = url.split("github.com/")[-1]
            else:
                return None
            
            # Remove .git suffix if present
            if repo_part.endswith(".git"):
                repo_part = repo_part[:-4]
            
            return repo_part
        except Exception as e:
            self.logger.error(f"Failed to extract repo name from URL: {e}")
        return None
    
    def initialize_git_repository(self) -> Tuple[bool, str]:
        """Initialize a new Git repository."""
        try:
            result = subprocess.run(
                ["git", "init"],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return True, "Git repository initialized"
            else:
                return False, result.stderr.strip()
        except Exception as e:
            return False, f"Failed to initialize Git repository: {str(e)}"
    
    def add_remote_origin(self, repo_url: str) -> Tuple[bool, str]:
        """Add remote origin to repository."""
        try:
            result = subprocess.run(
                ["git", "remote", "add", "origin", repo_url],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return True, f"Remote origin added: {repo_url}"
            else:
                return False, result.stderr.strip()
        except Exception as e:
            return False, f"Failed to add remote origin: {str(e)}"
    
    def get_current_branch(self) -> Optional[str]:
        """Get the current Git branch."""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Failed to get current branch: {e}")
        return None
    
    def has_commits(self) -> bool:
        """Check if repository has any commits."""
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-1"],
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
