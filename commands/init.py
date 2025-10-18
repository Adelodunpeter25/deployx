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
            questionary.Choice("Vercel (Serverless deployment)", "vercel"),
            questionary.Choice("Netlify (JAMstack hosting)", "netlify"),
            questionary.Choice("Railway (Full-stack apps)", "railway"),
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
    elif platform == "vercel":
        platform_config = _configure_vercel(project_path, summary)
        if platform_config is None:
            return False
    elif platform == "netlify":
        platform_config = _configure_netlify(project_path, summary)
        if platform_config is None:
            return False
    elif platform == "railway":
        platform_config = _configure_railway(project_path, summary)
        if platform_config is None:
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
    token_value = questionary.password(
        "Enter your GitHub personal access token:"
    ).ask()
    
    if not token_value:
        error("Token required for GitHub Pages deployment")
        return None
    
    # Save token to .deployx_token file
    project_path_obj = Path(project_path)
    token_file = project_path_obj / ".deployx_token"
    try:
        with open(token_file, 'w') as f:
            f.write(token_value)
        # Set restrictive permissions (owner read/write only)
        os.chmod(token_file, 0o600)
        success("Token saved securely to .deployx_token")
        
        # Add to .gitignore if it exists
        gitignore_path = project_path_obj / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                gitignore_content = f.read()
            if '.deployx_token' not in gitignore_content:
                with open(gitignore_path, 'a') as f:
                    f.write('\n.deployx_token\n')
                info("Added .deployx_token to .gitignore")
        else:
            # Create .gitignore with token file
            with open(gitignore_path, 'w') as f:
                f.write('.deployx_token\n')
            info("Created .gitignore with .deployx_token")
            
    except Exception as e:
        error(f"Failed to save token: {str(e)}")
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
        "branch": branch
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

def _configure_vercel(project_path: str, summary: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Configure Vercel settings"""
    info("⚙️  Configuring Vercel...")
    
    # Get Vercel token
    token_value = questionary.password(
        "Enter your Vercel token:"
    ).ask()
    
    if not token_value:
        error("Token required for Vercel deployment")
        return None
    
    # Save token
    if not _save_platform_token(project_path, "vercel", token_value):
        return None
    
    return {}

def _configure_netlify(project_path: str, summary: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Configure Netlify settings"""
    info("⚙️  Configuring Netlify...")
    
    # Get Netlify token
    token_value = questionary.password(
        "Enter your Netlify token:"
    ).ask()
    
    if not token_value:
        error("Token required for Netlify deployment")
        return None
    
    # Save token
    if not _save_platform_token(project_path, "netlify", token_value):
        return None
    
    # Optional site ID
    site_id = questionary.text(
        "Site ID (optional, leave empty to create new):"
    ).ask()
    
    config = {}
    if site_id:
        config["site_id"] = site_id
    
    return config

def _configure_railway(project_path: str, summary: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Configure Railway settings"""
    info("⚙️  Configuring Railway...")
    
    # Get Railway token
    token_value = questionary.password(
        "Enter your Railway token:"
    ).ask()
    
    if not token_value:
        error("Token required for Railway deployment")
        return None
    
    # Save token
    if not _save_platform_token(project_path, "railway", token_value):
        return None
    
    # Optional project ID
    project_id = questionary.text(
        "Project ID (optional, leave empty to create new):"
    ).ask()
    
    config = {}
    if project_id:
        config["project_id"] = project_id
    
    return config

def _save_platform_token(project_path: str, platform: str, token: str) -> bool:
    """Save platform token to file"""
    project_path_obj = Path(project_path)
    token_file = project_path_obj / f".deployx_{platform}_token"
    
    try:
        with open(token_file, 'w') as f:
            f.write(token)
        os.chmod(token_file, 0o600)
        success(f"Token saved securely to .deployx_{platform}_token")
        
        # Add to .gitignore
        gitignore_path = project_path_obj / ".gitignore"
        token_entry = f".deployx_{platform}_token"
        
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                gitignore_content = f.read()
            if token_entry not in gitignore_content:
                with open(gitignore_path, 'a') as f:
                    f.write(f'\n{token_entry}\n')
        else:
            with open(gitignore_path, 'w') as f:
                f.write(f'{token_entry}\n')
        
        return True
        
    except Exception as e:
        error(f"Failed to save token: {str(e)}")
        return False

def _show_next_steps() -> None:
    """Show next steps after successful configuration"""
    print("\n🎉 Setup complete! Next steps:")
    print("   1. Run 'deployx deploy' to deploy your project")
    print("   2. Check deployment status with 'deployx status'")
    print("   3. Edit 'deployx.yml' to customize settings")
    print("\n💡 Make sure your tokens have the required permissions!")