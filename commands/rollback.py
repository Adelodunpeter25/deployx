"""
Rollback command for DeployX.

Reverts to a previous successful deployment by redeploying
from a stored snapshot in deployment history.

Example:
    >>> from commands.rollback import rollback_command
    >>> rollback_command("./my-project")
"""

import questionary
from typing import Optional, Dict, Any

from utils.ui import header, success, error, info, warning
from utils.config import Config
from commands.history import _load_history
from platforms.factory import get_platform


def rollback_command(project_path: str = ".", target_index: Optional[int] = None) -> bool:
    """
    Rollback to a previous deployment.
    
    Shows deployment history and allows user to select which
    deployment to rollback to. Redeploys using the previous
    configuration and commit.
    
    Args:
        project_path: Path to project directory (default: current directory)
        target_index: Specific deployment index to rollback to (default: prompt user)
    
    Returns:
        True if rollback successful, False otherwise
    
    Example:
        >>> rollback_command("./my-app")
        True
    """
    header("Rollback Deployment")
    
    config = Config(project_path)
    
    if not config.exists():
        error("❌ No configuration found. Run 'deployx init' first.")
        return False
    
    # Load deployment history
    history = _load_history(project_path)
    
    if not history:
        error("❌ No deployment history found")
        info("💡 Deploy at least once before using rollback")
        return False
    
    # Filter successful deployments only
    successful_deployments = [
        d for d in history 
        if d.get('status', '').lower() in ['success', 'ready']
    ]
    
    if not successful_deployments:
        error("❌ No successful deployments found in history")
        return False
    
    # Get current deployment (last in history)
    current_deployment = history[-1] if history else None
    
    # Select target deployment
    if target_index is not None:
        if target_index < 1 or target_index > len(successful_deployments):
            error(f"❌ Invalid deployment index: {target_index}")
            return False
        target_deployment = successful_deployments[-(target_index)]
    else:
        target_deployment = _select_deployment(successful_deployments, current_deployment)
        if not target_deployment:
            info("Rollback cancelled")
            return False
    
    # Confirm rollback
    if not _confirm_rollback(current_deployment, target_deployment):
        info("Rollback cancelled")
        return False
    
    # Execute rollback
    return _execute_rollback(project_path, target_deployment, config)


def _select_deployment(deployments: list, current: Optional[Dict]) -> Optional[Dict]:
    """
    Prompt user to select deployment to rollback to.
    
    Args:
        deployments: List of successful deployments
        current: Current deployment info
    
    Returns:
        Selected deployment dict or None if cancelled
    """
    from datetime import datetime
    
    # Create choices (exclude current deployment)
    choices = []
    for i, deployment in enumerate(reversed(deployments), 1):
        # Skip if this is the current deployment
        if current and deployment.get('timestamp') == current.get('timestamp'):
            continue
        
        timestamp = deployment.get('timestamp', 'Unknown')
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            formatted_time = timestamp
        
        commit = deployment.get('commit_id', 'N/A')[:7]
        url = deployment.get('url', 'N/A')
        
        choice_text = f"{formatted_time} | Commit: {commit} | {url}"
        choices.append(questionary.Choice(choice_text, value=deployment))
    
    if not choices:
        error("❌ No previous deployments available for rollback")
        return None
    
    info(f"📋 Found {len(choices)} previous deployment(s)")
    
    selected = questionary.select(
        "Select deployment to rollback to:",
        choices=choices
    ).ask()
    
    return selected


def _confirm_rollback(current: Optional[Dict], target: Dict) -> bool:
    """
    Confirm rollback action with user.
    
    Args:
        current: Current deployment info
        target: Target deployment to rollback to
    
    Returns:
        True if confirmed, False otherwise
    """
    from datetime import datetime
    
    print("\n⚠️  Rollback Summary:")
    
    if current:
        current_time = current.get('timestamp', 'Unknown')
        try:
            dt = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
            current_time = dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            pass
        print(f"   Current: {current_time}")
        if current.get('commit_id'):
            print(f"   Commit: {current.get('commit_id')[:7]}")
    
    target_time = target.get('timestamp', 'Unknown')
    try:
        dt = datetime.fromisoformat(target_time.replace('Z', '+00:00'))
        target_time = dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        pass
    
    print(f"\n   Rolling back to: {target_time}")
    if target.get('commit_id'):
        print(f"   Commit: {target.get('commit_id')[:7]}")
    if target.get('url'):
        print(f"   URL: {target.get('url')}")
    
    print("\n⚠️  This will:")
    print("   • Redeploy the selected version")
    print("   • Overwrite current deployment")
    print("   • Update live site immediately")
    
    return questionary.confirm(
        "\n🔄 Proceed with rollback?",
        default=False
    ).ask()


def _execute_rollback(project_path: str, target: Dict, config: Config) -> bool:
    """
    Execute the rollback by redeploying target version.
    
    Args:
        project_path: Path to project directory
        target: Target deployment to rollback to
        config: Config object
    
    Returns:
        True if successful, False otherwise
    """
    info("🔄 Starting rollback...")
    
    # Load current config
    config_data = config.load()
    platform_name = config_data.get('platform')
    platform_config = config_data.get(platform_name, {})
    
    # Get platform instance
    try:
        platform = get_platform(platform_name, platform_config)
    except Exception as e:
        error(f"❌ Failed to initialize platform: {str(e)}")
        return False
    
    # Check if we need to checkout specific commit
    commit_id = target.get('commit_id')
    if commit_id:
        if not _checkout_commit(project_path, commit_id):
            warning("⚠️  Could not checkout commit, proceeding with current code")
    
    # Validate credentials
    info("🔐 Validating credentials...")
    valid, message = platform.validate_credentials()
    if not valid:
        error(f"❌ Credential validation failed: {message}")
        return False
    
    # Prepare deployment
    build_config = config_data.get('build', {})
    build_command = build_config.get('command')
    output_dir = build_config.get('output', '.')
    
    info("🔨 Preparing deployment...")
    prepared, prep_message = platform.prepare_deployment(
        project_path, build_command, output_dir
    )
    
    if not prepared:
        error(f"❌ Preparation failed: {prep_message}")
        return False
    
    # Execute deployment
    info("🚀 Executing rollback deployment...")
    result = platform.execute_deployment(project_path, output_dir)
    
    if result.success:
        success("✅ Rollback successful!")
        if result.url:
            info(f"🌐 Live URL: {result.url}")
        
        # Record rollback in history
        from commands.history import add_to_history
        add_to_history(project_path, {
            'platform': platform_name,
            'status': 'success',
            'url': result.url,
            'deployment_id': result.deployment_id,
            'commit_id': commit_id,
            'rollback': True,
            'rollback_from': target.get('timestamp')
        })
        
        return True
    else:
        error(f"❌ Rollback failed: {result.message}")
        return False


def _checkout_commit(project_path: str, commit_id: str) -> bool:
    """
    Checkout specific git commit.
    
    Args:
        project_path: Path to project directory
        commit_id: Git commit hash
    
    Returns:
        True if successful, False otherwise
    """
    try:
        from git import Repo
        
        repo = Repo(project_path)
        
        # Check for uncommitted changes
        if repo.is_dirty():
            warning("⚠️  Uncommitted changes detected")
            stash = questionary.confirm(
                "Stash changes before rollback?",
                default=True
            ).ask()
            
            if stash:
                repo.git.stash('save', 'DeployX rollback stash')
                info("📦 Changes stashed")
            else:
                error("❌ Cannot rollback with uncommitted changes")
                return False
        
        # Checkout commit
        info(f"📝 Checking out commit {commit_id[:7]}...")
        repo.git.checkout(commit_id)
        success(f"✅ Checked out commit {commit_id[:7]}")
        
        return True
        
    except Exception as e:
        error(f"❌ Git checkout failed: {str(e)}")
        return False
