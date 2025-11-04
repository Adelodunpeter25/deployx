"""
GitHub Pages deployment execution functionality.
"""
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional
from git import Repo, GitCommandError

from core.logging import get_logger
from utils.errors import handle_build_error, handle_git_error
from ..base import DeploymentResult

class GitHubDeployment:
    """Handles GitHub Pages deployment execution."""
    
    def __init__(self, repo_name: str, method: str = "branch", branch: str = "gh-pages"):
        self.repo_name = repo_name
        self.method = method
        self.branch = branch
        self.logger = get_logger(__name__)
    
    def deploy_to_branch(self, project_path: str, output_dir: str) -> DeploymentResult:
        """Deploy to GitHub Pages using branch method."""
        try:
            project_path = Path(project_path)
            output_path = project_path / output_dir
            
            if not output_path.exists():
                error = handle_build_error(f"Build output directory not found: {output_path}")
                return DeploymentResult(
                    success=False,
                    message=error.message,
                    url=None,
                    deployment_id=None
                )
            
            # Initialize or get existing repository
            try:
                repo = Repo(project_path)
            except:
                repo = Repo.init(project_path)
            
            # Create and switch to deployment branch
            try:
                # Check if branch exists locally
                if self.branch in [ref.name.split('/')[-1] for ref in repo.refs]:
                    repo.git.checkout(self.branch)
                else:
                    # Create new branch
                    repo.git.checkout('-b', self.branch)
            except GitCommandError:
                # Branch might exist remotely, try to checkout
                try:
                    repo.git.checkout('-b', self.branch, f'origin/{self.branch}')
                except GitCommandError:
                    repo.git.checkout('--orphan', self.branch)
            
            # Clear branch content (keep .git and other important files)
            protected_items = {'.git', output_dir, '.gitignore', 'CNAME'}
            
            for item in project_path.iterdir():
                if item.name not in protected_items:
                    try:
                        if item.is_dir():
                            shutil.rmtree(item, ignore_errors=True)
                        else:
                            item.unlink(missing_ok=True)
                    except (OSError, PermissionError) as e:
                        self.logger.warning(f"Could not remove {item.name}: {e}")
                        continue
            
            # Copy build output to root
            for item in output_path.iterdir():
                dest_path = project_path / item.name
                try:
                    if item.is_dir():
                        if dest_path.exists():
                            shutil.rmtree(dest_path, ignore_errors=True)
                        shutil.copytree(item, dest_path)
                    else:
                        shutil.copy2(item, dest_path)
                except (OSError, PermissionError) as e:
                    self.logger.warning(f"Could not copy {item.name}: {e}")
                    continue
            
            # Add, commit and push
            repo.git.add('.')
            
            try:
                repo.git.commit('-m', 'Deploy to GitHub Pages')
            except GitCommandError as e:
                if "nothing to commit" in str(e):
                    return DeploymentResult(
                        success=True,
                        message="No changes to deploy",
                        url=self._generate_pages_url(),
                        deployment_id=None
                    )
                raise
            
            # Push to remote
            try:
                origin = repo.remote('origin')
                origin.push(refspec=f'{self.branch}:{self.branch}', force=True)
            except Exception as e:
                error = handle_git_error(f"Failed to push to remote: {str(e)}")
                return DeploymentResult(
                    success=False,
                    message=error.message,
                    url=None,
                    deployment_id=None
                )
            
            return DeploymentResult(
                success=True,
                message=f"Successfully deployed to GitHub Pages (branch: {self.branch})",
                url=self._generate_pages_url(),
                deployment_id=None
            )
            
        except Exception as e:
            error = handle_git_error(f"Deployment failed: {str(e)}")
            return DeploymentResult(
                success=False,
                message=error.message,
                url=None,
                deployment_id=None
            )
    
    def deploy_to_docs_folder(self, project_path: str, output_dir: str) -> DeploymentResult:
        """Deploy to GitHub Pages using docs folder method."""
        try:
            project_path = Path(project_path)
            output_path = project_path / output_dir
            docs_path = project_path / "docs"
            
            if not output_path.exists():
                error = handle_build_error(f"Build output directory not found: {output_path}")
                return DeploymentResult(
                    success=False,
                    message=error.message,
                    url=None,
                    deployment_id=None
                )
            
            # Create docs directory and copy build output
            if docs_path.exists():
                shutil.rmtree(docs_path)
            shutil.copytree(output_path, docs_path)
            
            # Commit and push changes
            repo = Repo(project_path)
            repo.git.add('docs/')
            repo.git.commit('-m', 'Deploy to GitHub Pages (docs folder)')
            
            origin = repo.remote('origin')
            origin.push()
            
            return DeploymentResult(
                success=True,
                message="Successfully deployed to GitHub Pages (docs folder)",
                url=self._generate_pages_url(),
                deployment_id=None
            )
            
        except Exception as e:
            error = handle_git_error(f"Deployment failed: {str(e)}")
            return DeploymentResult(
                success=False,
                message=error.message,
                url=None,
                deployment_id=None
            )
    
    def _generate_pages_url(self) -> str:
        """Generate GitHub Pages URL."""
        if not self.repo_name:
            return ""
        
        parts = self.repo_name.split('/')
        if len(parts) != 2:
            return ""
        
        username, repo = parts
        
        # Special case for username.github.io repositories
        if repo == f"{username}.github.io":
            return f"https://{username}.github.io"
        else:
            return f"https://{username}.github.io/{repo}"
