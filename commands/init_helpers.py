"""
Helper functions for initialization command.

Extracted from init.py to keep functions focused and maintainable.
Handles token management, git detection, and platform-specific prompts.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import questionary
from git import Repo, InvalidGitRepositoryError

from utils.ui import success, error, info
from core.constants import (
    TOKEN_FILE_PERMISSIONS,
)


def save_token_to_file(project_path: str, platform: str, token: str) -> bool:
    """
    Save platform token to secure file.
    
    Creates .deployx_{platform}_token file with restricted permissions
    and automatically adds it to .gitignore.
    
    Args:
        project_path: Path to project directory
        platform: Platform name (github, vercel, etc.)
        token: API token to save
    
    Returns:
        True if successful, False otherwise
    """
    project_path_obj = Path(project_path)
    token_filename = f".deployx_{platform}_token" if platform != "github" else ".deployx_token"
    token_file = project_path_obj / token_filename
    
    try:
        # Write token file
        with open(token_file, 'w') as f:
            f.write(token)
        
        # Set restrictive permissions (owner read/write only)
        os.chmod(token_file, TOKEN_FILE_PERMISSIONS)
        success(f"Token saved securely to {token_filename}")
        
        # Add to .gitignore
        _add_to_gitignore(project_path_obj, token_filename)
        
        return True
        
    except Exception as e:
        error(f"Failed to save token: {str(e)}")
        return False


def _add_to_gitignore(project_path: Path, entry: str) -> None:
    """
    Add entry to .gitignore file.
    
    Creates .gitignore if it doesn't exist, or appends to existing file
    if entry is not already present.
    
    Args:
        project_path: Path to project directory
        entry: Entry to add to .gitignore
    """
    gitignore_path = project_path / ".gitignore"
    
    if gitignore_path.exists():
        # Check if entry already exists
        with open(gitignore_path, 'r') as f:
            gitignore_content = f.read()
        
        if entry not in gitignore_content:
            with open(gitignore_path, 'a') as f:
                f.write(f'\n{entry}\n')
            info(f"Added {entry} to .gitignore")
    else:
        # Create new .gitignore
        with open(gitignore_path, 'w') as f:
            f.write(f'{entry}\n')
        info(f"Created .gitignore with {entry}")


def detect_git_repository(project_path: str) -> Optional[str]:
    """
    Auto-detect GitHub repository from git remote.
    
    Parses git remote URL to extract owner/repo format.
    Supports both SSH and HTTPS URLs.
    
    Args:
        project_path: Path to project directory
    
    Returns:
        Repository in "owner/repo" format, or None if not found
    
    Example:
        >>> detect_git_repository("./my-project")
        'username/my-project'
    """
    try:
        repo = Repo(project_path)
        
        # Get origin remote URL
        if 'origin' not in repo.remotes:
            return None
        
        url = repo.remotes.origin.url
        
        # Only process GitHub URLs
        if 'github.com' not in url:
            return None
        
        # Parse SSH format: git@github.com:owner/repo.git
        if url.startswith('git@'):
            repo_part = url.split(':')[1].replace('.git', '')
        # Parse HTTPS format: https://github.com/owner/repo.git
        else:
            repo_part = url.split('github.com/')[1].replace('.git', '')
        
        return repo_part
        
    except (InvalidGitRepositoryError, Exception):
        return None


def get_project_name_from_files(project_path: str) -> str:
    """
    Extract project name from package.json or directory name.
    
    Args:
        project_path: Path to project directory
    
    Returns:
        Project name string
    """
    # Try to get from package.json
    package_json_path = Path(project_path) / "package.json"
    if package_json_path.exists():
        try:
            import json
            with open(package_json_path) as f:
                data = json.load(f)
                if 'name' in data:
                    return data['name']
        except Exception:
            pass
    
    # Fallback to directory name
    return Path(project_path).resolve().name


def prompt_for_token(platform: str, token_url: str) -> Optional[str]:
    """
    Prompt user for platform API token.
    
    Args:
        platform: Platform name for display
        token_url: URL where user can generate token
    
    Returns:
        Token string or None if cancelled
    """
    token_value = questionary.password(
        f"Enter your {platform} token:\n"
        f"🔗 Get it from: {token_url}\n"
        f"🔑 Needs: Full access\n"
    ).ask()
    
    if not token_value:
        error(f"Token required for {platform} deployment")
        return None
    
    return token_value


def get_start_command_suggestion(project_type: str) -> str:
    """
    Suggest start command based on project type.
    
    Args:
        project_type: Type of project (django, flask, nodejs, etc.)
    
    Returns:
        Suggested start command
    """
    suggestions = {
        'django': 'python manage.py runserver 0.0.0.0:$PORT',
        'flask': 'python app.py',
        'fastapi': 'uvicorn main:app --host 0.0.0.0 --port $PORT',
        'nodejs': 'npm start',
        'react': 'npm start',
        'nextjs': 'npm start'
    }
    
    return suggestions.get(project_type, 'npm start')
