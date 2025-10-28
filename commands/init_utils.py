"""
Utility functions for initialization command.

Handles project name detection, git repository detection,
build settings configuration, and display functions.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
import questionary
from git import Repo, InvalidGitRepositoryError


def detect_git_repository(project_path: str) -> Optional[str]:
    """
    Auto-detect GitHub repository from git remote.
    
    Parses git remote URL to extract owner/repo format.
    Supports both SSH and HTTPS URL formats.
    
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


def get_project_name(project_path: str, summary: Dict[str, Any]) -> str:
    """
    Get project name from package.json or directory name.
    
    Tries to extract name from package.json first, falls back
    to directory name if not found.
    
    Args:
        project_path: Path to project directory
        summary: Project detection summary (unused but kept for compatibility)
    
    Returns:
        Project name string
    """
    # Try to get from package.json
    package_json_path = Path(project_path) / "package.json"
    if package_json_path.exists():
        try:
            with open(package_json_path) as f:
                data = json.load(f)
                if 'name' in data:
                    return data['name']
        except Exception:
            pass
    
    # Fallback to directory name
    return Path(project_path).resolve().name


def configure_build_settings(summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Configure build command and output directory.
    
    Prompts user to confirm detected build settings or enter custom values.
    
    Args:
        summary: Project detection summary with detected build settings
    
    Returns:
        Dict with 'command' and 'output' keys
    """
    # Build command
    build_command = summary.get('build_command')
    if build_command:
        use_detected = questionary.confirm(
            f"Use detected build command: '{build_command}'?",
            default=True
        ).ask()
        
        if not use_detected:
            build_command = questionary.text(
                "Build command (leave empty if none):"
            ).ask()
    else:
        build_command = questionary.text(
            "Build command (leave empty if none):"
        ).ask()
    
    # Output directory
    output_dir = questionary.text(
        "Output directory:",
        default=summary.get('output_dir', '.')
    ).ask()
    
    return {
        "command": build_command or None,
        "output": output_dir
    }


def display_detection_results(summary: Dict[str, Any]) -> None:
    """
    Display project detection results to user.
    
    Shows detected project type, framework, package manager,
    build command, and output directory.
    
    Args:
        summary: Project detection summary dictionary
    """
    print("📋 Project detected:")
    print(f"   Type: {summary['type']}")
    
    if summary['framework']:
        print(f"   Framework: {summary['framework']}")
    
    print(f"   Package Manager: {summary['package_manager']}")
    
    if summary['build_command']:
        print(f"   Build Command: {summary['build_command']}")
    
    print(f"   Output Directory: {summary['output_dir']}")
    print()


def show_next_steps() -> None:
    """
    Display next steps after successful configuration.
    
    Shows user what commands to run next and helpful tips.
    """
    print("\n🎉 Setup complete! Next steps:")
    print("   1. Run 'deployx deploy' to deploy your project")
    print("   2. Check deployment status with 'deployx status'")
    print("   3. Edit 'deployx.yml' to customize settings")
    print("\n💡 Make sure your tokens have the required permissions!")
