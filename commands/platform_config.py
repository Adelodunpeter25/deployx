"""
Platform-specific configuration handlers for init command.

Each platform has its own configuration function that prompts
for necessary settings and returns a configuration dictionary.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import questionary

from utils.ui import success, error, info
from core.constants import TOKEN_FILE_PERMISSIONS


def configure_github(project_path: str, summary: Dict[str, Any], 
                    detect_repo_func, get_name_func) -> Optional[Dict[str, Any]]:
    """
    Configure GitHub Pages deployment settings.
    
    Prompts for GitHub token, repository name, and deployment method.
    Saves token securely and adds to .gitignore.
    
    Args:
        project_path: Path to project directory
        summary: Project detection summary
        detect_repo_func: Function to detect git repository
        get_name_func: Function to get project name
    
    Returns:
        Dict with GitHub configuration or None if cancelled
    """
    # Get GitHub token
    token_value = questionary.password(
        "Enter your GitHub personal access token:\n"
        "🔗 Get it from: github.com/settings/tokens\n"
        "🔑 Needs: repo, workflow permissions\n"
        "🏷️  Format: ghp_xxxxxxxxxxxx\n"
    ).ask()
    
    if not token_value:
        error("Token required for GitHub Pages deployment")
        return None
    
    # Save token securely
    if not _save_github_token(project_path, token_value):
        return None
    
    # Auto-detect or prompt for repository
    repo_name = _get_repository_name(project_path, detect_repo_func)
    if not repo_name:
        return None
    
    # Get deployment method
    method = questionary.select(
        "Deployment method:",
        choices=[
            questionary.Choice("Branch (gh-pages) - Recommended", "branch"),
            questionary.Choice("Docs folder (main branch)", "docs")
        ]
    ).ask()
    
    # Get branch name if using branch method
    branch = "gh-pages"
    if method == "branch":
        branch = questionary.text(
            "Target branch:",
            default="gh-pages"
        ).ask()
    
    return {
        "repo": repo_name,
        "method": method,
        "branch": branch
    }


def configure_vercel(project_path: str, summary: Dict[str, Any],
                    get_name_func) -> Optional[Dict[str, Any]]:
    """
    Configure Vercel deployment settings.
    
    Args:
        project_path: Path to project directory
        summary: Project detection summary
        get_name_func: Function to get project name
    
    Returns:
        Dict with Vercel configuration or None if cancelled
    """
    # Get Vercel token
    token_value = questionary.password(
        "Enter your Vercel token:\n"
        "🔗 Get it from: vercel.com/account/tokens\n"
        "🔑 Needs: Full access\n"
        "🏷️  Format: xxxxxxxxxx\n"
    ).ask()
    
    if not token_value:
        error("Token required for Vercel deployment")
        return None
    
    # Save token
    if not _save_platform_token(project_path, "vercel", token_value):
        return None
    
    # Project name
    project_name = questionary.text(
        "Project name (creates projectname.vercel.app):",
        default=get_name_func(project_path, summary).lower().replace('_', '-')
    ).ask()
    
    if not project_name:
        error("Project name is required")
        return None
    
    # Root directory for monorepos
    root_directory = questionary.text(
        "Root directory (leave empty if project is in root):"
    ).ask()
    
    config = {}
    if project_name:
        config["name"] = project_name
    if root_directory:
        config["root_directory"] = root_directory
    
    return config


def configure_netlify(project_path: str, summary: Dict[str, Any],
                     get_name_func) -> Optional[Dict[str, Any]]:
    """
    Configure Netlify deployment settings.
    
    Args:
        project_path: Path to project directory
        summary: Project detection summary
        get_name_func: Function to get project name
    
    Returns:
        Dict with Netlify configuration or None if cancelled
    """
    # Get Netlify token
    token_value = questionary.password(
        "Enter your Netlify Personal Access Token:\n"
        "🔗 Get it from: app.netlify.com/user/applications#personal-access-tokens\n"
        "🔑 Needs: Full access\n"
        "🏷️  Format: xxxxxxxxxx\n"
    ).ask()
    
    if not token_value:
        error("Token required for Netlify deployment")
        return None
    
    # Save token
    if not _save_platform_token(project_path, "netlify", token_value):
        return None
    
    # Site name (optional)
    site_name = questionary.text(
        "Site name (optional, leave empty for auto-generated):"
    ).ask()
    
    # Custom domain (optional)
    custom_domain = questionary.text(
        "Custom domain (optional):"
    ).ask()
    
    # Auto-deploy on git push
    auto_deploy = questionary.confirm(
        "Enable automatic deployments on git push?",
        default=True
    ).ask()
    
    config = {}
    if site_name:
        config["name"] = site_name
    if custom_domain:
        config["domain"] = custom_domain
    if auto_deploy is not None:
        config["auto_deploy"] = auto_deploy
    
    return config


def configure_railway(project_path: str, summary: Dict[str, Any],
                     get_name_func) -> Optional[Dict[str, Any]]:
    """
    Configure Railway deployment settings.
    
    Args:
        project_path: Path to project directory
        summary: Project detection summary
        get_name_func: Function to get project name
    
    Returns:
        Dict with Railway configuration or None if cancelled
    """
    # Get Railway token
    token_value = questionary.password(
        "Enter your Railway API token:\n"
        "🔗 Get it from: railway.app/account/tokens\n"
        "🔑 Needs: Full access\n"
        "🏷️  Format: xxxxxxxxxx\n"
    ).ask()
    
    if not token_value:
        error("Token required for Railway deployment")
        return None
    
    # Save token
    if not _save_platform_token(project_path, "railway", token_value):
        return None
    
    # Project name
    project_name = questionary.text(
        "Project name:",
        default=get_name_func(project_path, summary)
    ).ask()
    
    if not project_name:
        error("Project name is required")
        return None
    
    # Service name
    service_name = questionary.text(
        "Service name:",
        default="web"
    ).ask()
    
    if not service_name:
        error("Service name is required")
        return None
    
    # Application type
    app_type = questionary.select(
        "Application type:",
        choices=[
            questionary.Choice("Web service (needs port)", "web"),
            questionary.Choice("Worker (background jobs)", "worker"),
            questionary.Choice("Cron job (scheduled tasks)", "cron"),
            questionary.Choice("Static site", "static")
        ]
    ).ask()
    
    if not app_type:
        error("Application type is required")
        return None
    
    # Start command (for web services)
    start_command = None
    if app_type == "web":
        start_command = questionary.text(
            "Start command (how to run your app):",
            default=_get_start_command_suggestion(summary)
        ).ask()
    
    config = {
        "name": project_name,
        "service": service_name,
        "type": app_type
    }
    
    if start_command:
        config["start_command"] = start_command
    
    return config


def configure_render(project_path: str, summary: Dict[str, Any],
                    get_name_func) -> Optional[Dict[str, Any]]:
    """
    Configure Render deployment settings.
    
    Args:
        project_path: Path to project directory
        summary: Project detection summary
        get_name_func: Function to get project name
    
    Returns:
        Dict with Render configuration or None if cancelled
    """
    # Get Render API Key
    token_value = questionary.password(
        "Enter your Render API Key:\n"
        "🔗 Get it from: dashboard.render.com/account/api-keys\n"
        "🔑 Needs: Full access\n"
        "🏷️  Format: rnd_xxxxxxxxxxxx\n"
    ).ask()
    
    if not token_value:
        error("API Key required for Render deployment")
        return None
    
    # Save token
    if not _save_platform_token(project_path, "render", token_value):
        return None
    
    # Service type
    service_type = questionary.select(
        "What are you deploying?",
        choices=[
            questionary.Choice("Web Service (backend/full-stack)", "web_service"),
            questionary.Choice("Static Site (frontend only)", "static_site"),
            questionary.Choice("Background Worker", "worker"),
            questionary.Choice("Cron Job", "cron_job")
        ]
    ).ask()
    
    # Service name
    service_name = questionary.text(
        "Service/Site name (creates servicename.onrender.com):",
        default=get_name_func(project_path, summary).lower().replace('_', '-')
    ).ask()
    
    if not service_name:
        error("Service name is required")
        return None
    
    # Build command
    build_command = questionary.text(
        "Build command (leave empty to skip):",
        default=summary.get('build_command', '') or ''
    ).ask()
    
    # Environment
    environment = questionary.select(
        "Environment:",
        choices=[
            questionary.Choice("Node.js", "node"),
            questionary.Choice("Python", "python"),
            questionary.Choice("Ruby", "ruby"),
            questionary.Choice("Go", "go"),
            questionary.Choice("Rust", "rust"),
            questionary.Choice("Docker", "docker")
        ]
    ).ask()
    
    if not environment:
        error("Environment selection is required")
        return None
    
    config = {
        "name": service_name,
        "type": service_type,
        "environment": environment
    }
    
    if build_command:
        config["build_command"] = build_command
    
    # Start command (for web services and workers only)
    if service_type in ["web_service", "worker"]:
        start_command = questionary.text(
            "Start command (how to run your app):",
            default=_get_start_command_suggestion(summary)
        ).ask()
        
        if start_command:
            config["start_command"] = start_command
    
    return config


# Helper functions

def _save_github_token(project_path: str, token: str) -> bool:
    """Save GitHub token to .deployx_token file."""
    project_path_obj = Path(project_path)
    token_file = project_path_obj / ".deployx_token"
    
    try:
        with open(token_file, 'w') as f:
            f.write(token)
        # Set restrictive permissions (owner read/write only)
        os.chmod(token_file, TOKEN_FILE_PERMISSIONS)
        success("Token saved securely to .deployx_token")
        
        # Add to .gitignore
        _add_to_gitignore(project_path_obj, ".deployx_token")
        
        return True
        
    except Exception as e:
        error(f"Failed to save token: {str(e)}")
        return False


def _save_platform_token(project_path: str, platform: str, token: str) -> bool:
    """Save platform token to file."""
    project_path_obj = Path(project_path)
    token_file = project_path_obj / f".deployx_{platform}_token"
    
    try:
        with open(token_file, 'w') as f:
            f.write(token)
        os.chmod(token_file, TOKEN_FILE_PERMISSIONS)
        success(f"Token saved securely to .deployx_{platform}_token")
        
        # Add to .gitignore
        _add_to_gitignore(project_path_obj, f".deployx_{platform}_token")
        
        return True
        
    except Exception as e:
        error(f"Failed to save token: {str(e)}")
        return False


def _add_to_gitignore(project_path: Path, entry: str) -> None:
    """Add entry to .gitignore file."""
    gitignore_path = project_path / ".gitignore"
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            gitignore_content = f.read()
        if entry not in gitignore_content:
            with open(gitignore_path, 'a') as f:
                f.write(f'\n{entry}\n')
            info(f"Added {entry} to .gitignore")
    else:
        with open(gitignore_path, 'w') as f:
            f.write(f'{entry}\n')
        info(f"Created .gitignore with {entry}")


def _get_repository_name(project_path: str, detect_func) -> Optional[str]:
    """Get repository name from detection or user input."""
    repo_name = detect_func(project_path)
    
    if repo_name:
        info(f"🔍 Detected repository: {repo_name}")
        use_detected = questionary.confirm(
            "Use detected repository?",
            default=True
        ).ask()
        
        if not use_detected:
            repo_name = None
    
    if not repo_name:
        repo_name = questionary.text(
            "GitHub repository (owner/repo):",
            validate=lambda x: len(x.split('/')) == 2 or "Format: owner/repository"
        ).ask()
    
    return repo_name


def _get_start_command_suggestion(summary: Dict[str, Any]) -> str:
    """Suggest start command based on project type."""
    project_type = summary.get('type', '')
    
    suggestions = {
        'django': 'python manage.py runserver 0.0.0.0:$PORT',
        'flask': 'python app.py',
        'fastapi': 'uvicorn main:app --host 0.0.0.0 --port $PORT',
        'nodejs': 'npm start',
        'react': 'npm start',
        'nextjs': 'npm start'
    }
    
    return suggestions.get(project_type, 'npm start')
