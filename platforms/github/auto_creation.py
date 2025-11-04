"""
GitHub repository auto-creation functionality.
"""
import os
from typing import Tuple, Optional
from github import Github, GithubException
from pathlib import Path

from core.logging import get_logger
from utils.errors import handle_github_api_error, handle_auth_error
from .git_utils import GitUtils

class GitHubAutoCreation:
    """Handles automatic GitHub repository creation and setup."""
    
    def __init__(self, token: str):
        self.token = token
        self.github_client = Github(token) if token else None
        self.logger = get_logger(__name__)
        
    def should_create_repository(self, project_path: str = ".") -> Tuple[bool, str]:
        """
        Determine if we should auto-create a repository.
        
        Returns:
            Tuple of (should_create, reason)
        """
        git_utils = GitUtils(project_path)
        
        # Check if it's a git repository
        if not git_utils.is_git_repository():
            return True, "No git repository detected"
            
        # Check if it has a remote origin
        if not git_utils.has_remote_origin():
            return True, "Git repository exists but no remote origin configured"
            
        # Check if remote is GitHub
        remote_url = git_utils.get_remote_origin_url()
        if remote_url and "github.com" not in remote_url:
            return True, "Remote origin is not GitHub"
            
        return False, "Git repository with GitHub remote already exists"
    
    def auto_create_repository(self, project_name: str, project_path: str = ".") -> Tuple[bool, str, Optional[str]]:
        """
        Auto-create GitHub repository and configure it.
        
        Returns:
            Tuple of (success, message, repo_full_name)
        """
        if not self.github_client:
            return False, "GitHub token not available", None
            
        try:
            # Check if we should create
            should_create, reason = self.should_create_repository(project_path)
            if not should_create:
                self.logger.info(f"Skipping repository creation: {reason}")
                return True, reason, None
                
            # Get authenticated user
            user = self.github_client.get_user()
            suggested_name = self._generate_suggested_name(project_name, user.login)
            
            # Prompt user for repo name
            repo_name = self._prompt_for_repo_name(suggested_name)
            if not repo_name:
                return False, "Repository creation cancelled", None
            
            # Create repository
            repo = user.create_repo(
                name=repo_name,
                description=f"Deployed with DeployX - {project_name}",
                private=False,
                auto_init=False
            )
            
            # Enable GitHub Pages
            self._enable_github_pages(repo)
            
            # Configure git remote if needed
            self._configure_git_remote(repo.clone_url, project_path)
            
            return True, f"Created repository: {repo.full_name}", repo.full_name
            
        except GithubException as e:
            error = handle_github_api_error(e)
            return False, error.message, None
        except Exception as e:
            return False, f"Failed to create repository: {str(e)}", None
    
    def _generate_suggested_name(self, project_name: str, username: str) -> str:
        """Generate a suggested repository name from project folder."""
        base_name = project_name.lower().replace(" ", "-").replace("_", "-")
        
        # Check if repo exists and suggest alternative if needed
        try:
            self.github_client.get_repo(f"{username}/{base_name}")
            # If it exists, add suffix
            counter = 1
            while True:
                new_name = f"{base_name}-{counter}"
                try:
                    self.github_client.get_repo(f"{username}/{new_name}")
                    counter += 1
                except:
                    return new_name
        except:
            return base_name
    
    def _prompt_for_repo_name(self, suggested_name: str) -> Optional[str]:
        """Prompt user for repository name with suggestion."""
        try:
            print(f"\n📁 Repository name: {suggested_name}")
            user_input = input("   Use default (press Enter) or enter custom name: ").strip()
            
            if not user_input:
                return suggested_name
            
            # Validate custom name
            custom_name = user_input.lower().replace(" ", "-").replace("_", "-")
            return custom_name
            
        except KeyboardInterrupt:
            print("\n❌ Repository creation cancelled")
            return None
    
    def _enable_github_pages(self, repo) -> bool:
        """Enable GitHub Pages for the repository."""
        try:
            repo.create_pages_site(source={"branch": "gh-pages"})
            self.logger.info(f"Enabled GitHub Pages for {repo.full_name}")
            return True
        except Exception as e:
            self.logger.warning(f"Could not enable GitHub Pages: {str(e)}")
            return False
    
    def _configure_git_remote(self, clone_url: str, project_path: str) -> bool:
        """Configure git remote origin if needed."""
        try:
            git_utils = GitUtils(project_path)
            
            if not git_utils.is_git_repository():
                # Initialize git repository
                import subprocess
                subprocess.run(["git", "init"], cwd=project_path, check=True)
                
            if not git_utils.has_remote_origin():
                # Add remote origin
                import subprocess
                subprocess.run(
                    ["git", "remote", "add", "origin", clone_url],
                    cwd=project_path,
                    check=True
                )
                self.logger.info(f"Added remote origin: {clone_url}")
                
            return True
        except Exception as e:
            self.logger.error(f"Failed to configure git remote: {str(e)}")
            return False
