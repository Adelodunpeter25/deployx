import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from github import Github, GithubException
from git import Repo, GitCommandError
import requests

from utils.errors import (
    retry_with_backoff, handle_auth_error, handle_build_error, 
    handle_git_error, handle_github_api_error
)

from .base import BasePlatform, DeploymentResult, DeploymentStatus

class GitHubPlatform(BasePlatform):
    """GitHub Pages deployment platform"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.token = self._get_token()
        self.repo_name = config.get('repo')
        self.method = config.get('method', 'branch')  # 'branch' or 'docs'
        self.branch = config.get('branch', 'gh-pages')
        self.github_client = None
        self.repo_obj = None
    
    def _get_token(self) -> Optional[str]:
        """Get GitHub token from .deployx_token file or environment"""
        # Try .deployx_token file first
        token_file = Path('.deployx_token')
        if token_file.exists():
            try:
                with open(token_file, 'r') as f:
                    return f.read().strip()
            except Exception:
                pass
        
        # Fallback to environment variable
        return os.getenv('GITHUB_TOKEN')
    
    @retry_with_backoff(max_retries=3)
    def validate_credentials(self) -> Tuple[bool, str]:
        """Validate GitHub token and repository access"""
        if not self.token:
            error = handle_auth_error("github", "No token provided")
            return False, error.message
        
        if not self.repo_name:
            return False, "Repository name not configured"
        
        try:
            self.github_client = Github(self.token)
            
            # Validate token by fetching user info
            user = self.github_client.get_user()
            
            # Get repository and check write access
            self.repo_obj = self.github_client.get_repo(self.repo_name)
            
            # Check if user has write access
            try:
                permissions = self.repo_obj.get_collaborator_permission(user.login)
                if permissions not in ['admin', 'write']:
                    error = handle_auth_error("github", "Insufficient repository permissions")
                    return False, error.message
            except:
                # If we can't check permissions, try a simple operation
                try:
                    self.repo_obj.get_contents("README.md")
                except:
                    pass  # File might not exist, that's ok
            
            return True, f"GitHub credentials valid for user: {user.login}"
            
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            error = handle_auth_error("github", f"Network error: {str(e)}")
            return False, error.message
        except GithubException as e:
            error = handle_github_api_error(e)
            return False, error.message
        except Exception as e:
            error = handle_auth_error("github", str(e))
            return False, error.message
    
    def prepare_deployment(self, project_path: str, build_command: Optional[str], output_dir: str) -> Tuple[bool, str]:
        """Prepare deployment by building project and checking files"""
        project_path = Path(project_path)
        output_path = project_path / output_dir
        
        # Run build command if provided
        if build_command:
            try:
                cmd_parts = build_command.split()
                result = subprocess.run(
                    cmd_parts,
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.stdout:
                    print(f"Build output: {result.stdout}")
                    
            except subprocess.TimeoutExpired:
                error = handle_build_error(build_command, "", "Build timed out after 5 minutes")
                return False, error.message
            except subprocess.CalledProcessError as e:
                error = handle_build_error(build_command, e.stdout or "", e.stderr or "")
                return False, error.message
            except FileNotFoundError:
                error = handle_build_error(build_command, "", f"Command not found: {build_command}")
                return False, error.message
        
        # Check if output directory exists
        if not output_path.exists():
            return False, f"Output directory '{output_dir}' not found after build"
        
        # Verify files were generated
        files = [f for f in output_path.rglob('*') if f.is_file()]
        if not files:
            return False, f"No files generated in output directory '{output_dir}'"
        
        # Check for essential web files
        has_html = any(f.suffix == '.html' for f in files)
        if not has_html:
            return False, "No HTML files found. Ensure your build generates web content"
        
        return True, f"Build successful. {len(files)} files ready for deployment"
    
    def execute_deployment(self, project_path: str, output_dir: str) -> DeploymentResult:
        """Execute GitHub Pages deployment"""
        if self.method == 'branch':
            return self._deploy_to_branch(project_path, output_dir)
        else:
            return self._deploy_to_docs_folder(project_path, output_dir)
    
    def _deploy_to_branch(self, project_path: str, output_dir: str) -> DeploymentResult:
        """Deploy to gh-pages branch with full workflow"""
        try:
            project_path = Path(project_path)
            output_path = project_path / output_dir
            
            # Step 1: Repository Setup
            try:
                repo = Repo(project_path)
            except:
                return DeploymentResult(False, message="Not a git repository. Initialize with 'git init'")
            
            # Store current branch
            current_branch = repo.active_branch.name
            
            # Step 2: Branch Management
            try:
                # Check if gh-pages branch exists
                if self.branch in [ref.name for ref in repo.refs]:
                    repo.git.checkout(self.branch)
                else:
                    # Create orphan branch (no commit history)
                    repo.git.checkout('--orphan', self.branch)
                    repo.git.rm('-rf', '.', force=True)
            except GitCommandError as e:
                git_error = handle_git_error(e)
                return DeploymentResult(False, message=git_error.message)
            
            # Step 3: File Management
            try:
                # Clear existing files (except .git and special files)
                for item in project_path.iterdir():
                    if item.name not in ['.git', '.gitignore', 'CNAME', '.nojekyll']:
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                
                # Copy all files from build output, including hidden files
                for item in output_path.rglob('*'):
                    if item.is_file():
                        rel_path = item.relative_to(output_path)
                        dest_path = project_path / rel_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, dest_path)
                
                # Create .nojekyll file to bypass Jekyll processing
                (project_path / '.nojekyll').touch()
                
            except Exception as e:
                return DeploymentResult(False, message=f"File management failed: {str(e)}")
            
            # Step 4: Git Operations
            try:
                repo.git.add('.')
                
                # Check if there are changes to commit
                if repo.is_dirty() or repo.untracked_files:
                    commit_msg = f"Deploy to GitHub Pages - {repo.head.commit.hexsha[:7]}"
                    repo.git.commit('-m', commit_msg)
                    
                    # Push with force to handle history rewrites
                    repo.git.push('origin', self.branch, '--force')
                else:
                    # No changes, but still successful
                    pass
                    
            except GitCommandError as e:
                git_error = handle_git_error(e)
                return DeploymentResult(False, message=git_error.message)
            
            # Step 5: GitHub Pages Configuration
            try:
                if self.repo_obj:
                    # Enable GitHub Pages if not already enabled
                    try:
                        pages = self.repo_obj.get_pages_build()
                    except:
                        # Pages not enabled, try to enable it
                        try:
                            self.repo_obj.create_pages_site(source={"branch": self.branch, "path": "/"})
                        except:
                            pass  # May already be enabled or insufficient permissions
            except Exception:
                pass  # Non-critical, continue with deployment
            
            # Switch back to original branch
            try:
                repo.git.checkout(current_branch)
            except:
                pass  # Non-critical if we can't switch back
            
            # Step 6: URL Generation
            url = self._generate_pages_url()
            deployment_id = repo.head.commit.hexsha[:7]
            
            return DeploymentResult(
                True, 
                url=url, 
                message=f"Successfully deployed to {self.branch} branch",
                deployment_id=deployment_id
            )
            
        except Exception as e:
            return DeploymentResult(False, message=f"Deployment failed: {str(e)}")
    
    def _deploy_to_docs_folder(self, project_path: str, output_dir: str) -> DeploymentResult:
        """Deploy to docs folder in main branch"""
        try:
            project_path = Path(project_path)
            output_path = project_path / output_dir
            docs_path = project_path / 'docs'
            
            # Create docs folder and copy files
            if docs_path.exists():
                shutil.rmtree(docs_path)
            shutil.copytree(output_path, docs_path)
            
            # Commit and push
            repo = Repo(project_path)
            repo.git.add('docs/')
            repo.git.commit('-m', 'Deploy to GitHub Pages (docs folder)')
            repo.git.push('origin', 'main')
            
            url = f"https://{self.repo_name.split('/')[0]}.github.io/{self.repo_name.split('/')[1]}"
            return DeploymentResult(True, url=url, message="Deployed to docs folder")
            
        except Exception as e:
            return DeploymentResult(False, message=f"Deployment failed: {str(e)}")
    
    def get_status(self, deployment_id: Optional[str] = None) -> DeploymentStatus:
        """Get comprehensive GitHub Pages deployment status"""
        try:
            if not self.repo_obj:
                valid, msg = self.validate_credentials()
                if not valid:
                    return DeploymentStatus(status="error", message=msg)
            
            # Get latest deployment information
            try:
                pages_build = self.repo_obj.get_pages_build()
                
                # Get commit SHA of last deployment
                try:
                    branch_ref = self.repo_obj.get_git_ref(f"heads/{self.branch}")
                    last_commit = branch_ref.object.sha[:7]
                except:
                    last_commit = "unknown"
                
                # Check if Pages is enabled and get configuration
                try:
                    pages_info = self.repo_obj.get_pages_build()
                    pages_enabled = True
                    https_enforced = getattr(pages_info, 'https_enforced', False)
                except:
                    pages_enabled = False
                    https_enforced = False
                
                # Determine status
                if pages_build.status == "built":
                    status = "ready"
                    message = f"Deployment ready. Last commit: {last_commit}"
                elif pages_build.status == "building":
                    status = "building"
                    message = f"Deployment in progress. Commit: {last_commit}"
                else:
                    status = "error"
                    message = f"Deployment failed. Status: {pages_build.status}"
                
                return DeploymentStatus(
                    status=status,
                    url=self.get_url() if status == "ready" else None,
                    last_updated=pages_build.updated_at.isoformat() if pages_build.updated_at else None,
                    message=message
                )
                
            except Exception as e:
                if "404" in str(e):
                    return DeploymentStatus(
                        status="unknown", 
                        message="GitHub Pages not configured for this repository"
                    )
                else:
                    raise e
                
        except Exception as e:
            if "rate limit" in str(e).lower():
                return DeploymentStatus(status="error", message="GitHub API rate limit exceeded")
            else:
                return DeploymentStatus(status="error", message=f"Status check failed: {str(e)}")
    
    def _generate_pages_url(self) -> str:
        """Generate GitHub Pages URL with proper format"""
        owner, repo = self.repo_name.split('/')
        
        # Check for custom domain (CNAME file)
        try:
            if self.repo_obj:
                cname_content = self.repo_obj.get_contents("CNAME", ref=self.branch)
                custom_domain = cname_content.decoded_content.decode().strip()
                return f"https://{custom_domain}"
        except:
            pass
        
        # User/org repos (username.github.io)
        if repo.lower() == f"{owner.lower()}.github.io":
            return f"https://{owner.lower()}.github.io"
        
        # Project repos (username.github.io/repo-name)
        return f"https://{owner.lower()}.github.io/{repo}"
    
    def get_url(self) -> Optional[str]:
        """Get GitHub Pages URL"""
        if not self.repo_name:
            return None
        
        return self._generate_pages_url()

