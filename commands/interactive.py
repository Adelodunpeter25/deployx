"""
Interactive mode command for DeployX.

Provides a complete setup and deployment workflow in a single command.
Combines initialization and deployment with retry logic and error recovery.

This mode is ideal for:
- First-time users who want guided setup
- Quick deployments without multiple commands
- Ensuring deployment succeeds before exiting

Example:
    >>> from commands.interactive import interactive_command
    >>> success = interactive_command("./my-project")
"""

import questionary
from utils.ui import header, success, error, info, warning, smart_error_recovery
from utils.config import Config
from commands.init import init_command
from commands.deploy import deploy_command
from core.constants import MAX_DEPLOYMENT_ATTEMPTS


def interactive_command(project_path: str = ".") -> bool:
    """
    Interactive mode - complete setup and deployment workflow.
    
    Runs initialization if needed, then attempts deployment with
    retry logic and error recovery. Continues until deployment
    succeeds or user cancels.
    
    Args:
        project_path: Path to project directory (default: current directory)
    
    Returns:
        True if deployment successful, False otherwise
    
    Example:
        >>> interactive_command("./my-app")
        True
    """
    header("Interactive Mode")
    print("🎯 One CLI for all your deployments, stop memorizing platform-specific commands\n")
    
    config = Config(project_path)
    
    # Step 1: Handle configuration (init if needed)
    if not _handle_configuration(config, project_path):
        return False
    
    # Step 2: Deploy with retry loop
    return _deploy_with_retry(project_path)


def _handle_configuration(config: Config, project_path: str) -> bool:
    """
    Handle configuration setup.
    
    Checks if configuration exists and prompts to reconfigure if needed.
    Runs initialization for new projects.
    
    Args:
        config: Config object for the project
        project_path: Path to project directory
    
    Returns:
        True if configuration ready, False if setup failed/cancelled
    """
    if config.exists():
        # Configuration exists - ask if user wants to reconfigure
        reconfigure = questionary.confirm(
            "Configuration already exists. Do you want to reconfigure?",
            default=False
        ).ask()
        
        if reconfigure:
            if not _run_init(project_path, skip_header=True):
                return False
        else:
            info("Using existing configuration")
    else:
        # No configuration - run init
        if not _run_init(project_path, skip_header=True):
            return False
    
    return True


def _deploy_with_retry(project_path: str) -> bool:
    """
    Deploy with retry logic and error recovery.
    
    Attempts deployment up to MAX_DEPLOYMENT_ATTEMPTS times,
    with smart error recovery between attempts.
    
    Args:
        project_path: Path to project directory
    
    Returns:
        True if deployment successful, False otherwise
    """
    info("🚀 Starting deployment process")
    
    attempt = 1
    
    while attempt <= MAX_DEPLOYMENT_ATTEMPTS:
        if attempt > 1:
            print(f"\n🔄 Deployment attempt {attempt}/{MAX_DEPLOYMENT_ATTEMPTS}")
        
        # Attempt deployment
        if _run_deploy(project_path):
            success("🎉 Interactive deployment completed successfully!")
            _show_completion_message()
            return True
        
        # Deployment failed
        warning(f"❌ Deployment attempt {attempt} failed")
        
        # Try smart error recovery
        if smart_error_recovery("Deployment failed", "general"):
            info("🔄 Retrying after applying fixes...")
            if _run_deploy(project_path):
                success("🎉 Recovery successful! Deployment completed!")
                _show_completion_message()
                return True
        
        # Ask user what to do next (if not last attempt)
        if attempt < MAX_DEPLOYMENT_ATTEMPTS:
            action = _prompt_retry_action()
            
            if action == "retry":
                attempt += 1
                continue
            elif action == "reconfigure":
                info("🔧 Reconfiguring...")
                if not _run_init(project_path):
                    return False
                attempt += 1
                continue
            else:  # exit
                error("Deployment cancelled by user")
                return False
        else:
            # Last attempt failed
            error(f"❌ All {MAX_DEPLOYMENT_ATTEMPTS} deployment attempts failed")
            _show_failure_help()
            return False
    
    return False


def _prompt_retry_action() -> str:
    """
    Prompt user for action after failed deployment.
    
    Returns:
        Action string: "retry", "reconfigure", or "exit"
    """
    retry_options = [
        "Retry deployment",
        "Reconfigure and retry",
        "Exit"
    ]
    
    choice = questionary.select(
        "What would you like to do?",
        choices=retry_options
    ).ask()
    
    if choice == "Retry deployment":
        return "retry"
    elif choice == "Reconfigure and retry":
        return "reconfigure"
    else:
        return "exit"


def _run_init(project_path: str, skip_header: bool = False) -> bool:
    """
    Run initialization with error handling.
    
    Args:
        project_path: Path to project directory
        skip_header: Skip displaying header
    
    Returns:
        True if successful, False otherwise
    """
    try:
        return init_command(project_path, skip_header=skip_header)
    except Exception as e:
        error(f"❌ Initialization failed: {str(e)}")
        return False


def _run_deploy(project_path: str) -> bool:
    """
    Run deployment with error handling.
    
    Args:
        project_path: Path to project directory
    
    Returns:
        True if successful, False otherwise
    """
    try:
        return deploy_command(project_path)
    except Exception as e:
        error(f"❌ Deployment failed: {str(e)}")
        return False


def _show_completion_message() -> None:
    """
    Show completion message with next steps.
    
    Displays success banner and helpful information about
    what to do next.
    """
    print("\n" + "="*60)
    print("🎊 DEPLOYMENT COMPLETE! 🎊")
    print("="*60)
    print("\n💡 What's next:")
    print("   • Your site is now live and accessible")
    print("   • Use 'deployx status' to check deployment status")
    print("   • Use 'deployx deploy' for future updates")
    print("   • Edit 'deployx.yml' to customize settings")
    print("\n🔗 Bookmark your live URL for easy access!")


def _show_failure_help() -> None:
    """
    Show help message when all deployment attempts fail.
    
    Provides troubleshooting tips and next steps for users
    to resolve deployment issues.
    """
    print("\n🔧 Troubleshooting Help:")
    print("   • Check your internet connection")
    print("   • Verify your platform token is valid")
    print("   • Ensure repository exists and you have write access")
    print("   • Try running 'deployx init' and 'deployx deploy' separately")
    print("   • Use 'deployx --verbose deploy' for detailed error information")
    print("\n📞 Need help? Check the documentation or open an issue")
