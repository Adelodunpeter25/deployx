import os
from pathlib import Path
from typing import Dict, Any, Optional
import questionary
from git import Repo, InvalidGitRepositoryError

from utils.ui import header, success, error, info, warning, print_config_summary
from utils.config import Config, create_default_config
from utils.validator import validate_config
from detectors.project import detect_project, get_project_summary
from platforms.factory import PlatformFactory

def init_command(project_path: str = ".") -> bool:
    """Initialize DeployX configuration for a project"""
    
    # Display welcome message
    header("DeployX - Deploy Anywhere with One Command")
    print("🚀 Let's set up deployment for your project!\n")
    
    config = Config(project_path)
    
    # Check if configuration already exists
    if config.exists():
        warning("Configuration file already exists")
        overwrite = questionary.confirm(
            "Do you want to overwrite the existing configuration?",
            default=False
        ).ask()
        
        if not overwrite:
            info("Setup cancelled. Use 'deployx deploy' to deploy with existing config.")
            return False
    
    # Run project detection
    info("🔍 Analyzing your project...")
    project_info = detect_project(project_path)
    summary = get_project_summary(project_info)
    
    # Display detection results
    _display_detection_results(summary)
    
    # Get available platforms
    platforms = PlatformFactory.get_available_platforms()
    
    # Platform selection
    platform = questionary.select(
        "📡 Where do you want to deploy?",
        choices=[
            questionary.Choice("GitHub Pages (Free static hosting)", "github"),
            # Future platforms can be added here
        ]
    ).ask()
    
    if not platform:
        error("Platform selection cancelled")
        return False
    
    # Platform-specific configuration
    platform_config = {}
    if platform == "github":
        platform_config = _configure_github(project_path, summary)
        if not platform_config:
            return False
    
    # Confirm build settings
    build_config = _configure_build_settings(summary)
    
    # Create configuration
    config_data = create_default_config(
        _get_project_name(project_path, summary),
        summary['type'],
        platform
    )
    
    # Update with user inputs
    config_data['build'] = build_config
    config_data[platform] = platform_config
    
    # Validate configuration
    errors = validate_config(config_data)
    if errors:
        error("Configuration validation failed:")
        for err in errors:
            print(f"  • {err}")
        return False
    
    # Save configuration
    try:
        config.save(config_data)
        success("✅ Configuration saved to deployx.yml")
        
        # Display summary
        print_config_summary(config_data)
        
        # Show next steps
        _show_next_steps()
        
        return True
        
    except Exception as e:
        error(f"Failed to save configuration: {str(e)}")
        return False

def _display_detection_results(summary: Dict[str, Any]) -> None:
    """Display project detection results"""
    info("📋 Project Analysis Results:")
    print(f"   Type: {summary['type']}")
    
    if summary['framework']:
        print(f"   Framework: {summary['framework']}")
    
    print(f"   Package Manager: {summary['package_manager']}")
    
    if summary['build_command']:
        print(f"   Build Command: {summary['build_command']}")
    
    print(f"   Output Directory: {summary['output_dir']}")
    
    if summary['detected_files']:
        print(f"   Detected Files: {', '.join(summary['detected_files'])}")
    
    print()

def _configure_github(project_path: str, summary: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Configure GitHub Pages settings"""
    info("⚙️  Configuring GitHub Pages...")
    
    # Get GitHub token
    token_env = questionary.text(
        "Environment variable for GitHub token:",
        default="GITHUB_TOKEN"
    ).ask()
    
    if not token_env:
        return None
    
    # Check if token exists
    if not os.getenv(token_env):
        warning(f"Environment variable '{token_env}' not found")
        set_now = questionary.confirm(
            f"Do you want to set {token_env} now?",
            default=True
        ).ask()
        
        if set_now:
            token_value = questionary.password(
                f"Enter your GitHub personal access token:"
            ).ask()
            
            if token_value:
                os.environ[token_env] = token_value
                success(f"Token set for this session")
            else:
                error("Token required for GitHub Pages deployment")
                return None
    
    # Auto-detect repository from git remote
    repo_name = _detect_git_repository(project_path)
    
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
    
    if not repo_name:
        return None
    
    # Deployment method
    method = questionary.select(
        "Deployment method:",
        choices=[
            questionary.Choice("Branch (gh-pages) - Recommended", "branch"),
            questionary.Choice("Docs folder (main branch)", "docs")
        ]
    ).ask()
    
    # Branch configuration
    branch = "gh-pages"
    if method == "branch":
        branch = questionary.text(
            "Target branch:",
            default="gh-pages"
        ).ask()
    
    return {
        "repo": repo_name,
        "method": method,
        "branch": branch,
        "token_env": token_env
    }

def _configure_build_settings(summary: Dict[str, Any]) -> Dict[str, Any]:
    """Configure build settings"""
    info("🔧 Configuring build settings...")
    
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

def _detect_git_repository(project_path: str) -> Optional[str]:
    """Auto-detect GitHub repository from git remote"""
    try:
        repo = Repo(project_path)
        
        # Get origin remote URL
        if 'origin' in repo.remotes:
            url = repo.remotes.origin.url
            
            # Parse GitHub URL
            if 'github.com' in url:
                # Handle both SSH and HTTPS URLs
                if url.startswith('git@'):
                    # SSH: git@github.com:owner/repo.git
                    repo_part = url.split(':')[1].replace('.git', '')
                else:
                    # HTTPS: https://github.com/owner/repo.git
                    repo_part = url.split('github.com/')[1].replace('.git', '')
                
                return repo_part
                
    except (InvalidGitRepositoryError, Exception):
        pass
    
    return None

def _get_project_name(project_path: str, summary: Dict[str, Any]) -> str:
    """Get project name from directory or package.json"""
    # Try to get from package.json
    package_json_path = Path(project_path) / "package.json"
    if package_json_path.exists():
        try:
            import json
            with open(package_json_path) as f:
                data = json.load(f)
                if 'name' in data:
                    return data['name']
        except:
            pass
    
    # Fallback to directory name
    return Path(project_path).resolve().name

def _show_next_steps() -> None:
    """Show next steps after successful configuration"""
    print("\n🎉 Setup complete! Next steps:")
    print("   1. Run 'deployx deploy' to deploy your project")
    print("   2. Check deployment status with 'deployx status'")
    print("   3. Edit 'deployx.yml' to customize settings")
    print("\n💡 Make sure your GitHub token has repository permissions!")