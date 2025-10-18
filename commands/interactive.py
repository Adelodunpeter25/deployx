import questionary
from utils.ui import header, success, error, info, warning
from utils.config import Config
from commands.init import init_command
from commands.deploy import deploy_command

def interactive_command(project_path: str = ".") -> bool:
    """Interactive mode - complete setup and deployment workflow"""
    
    header("DeployX Interactive Mode")
    print("🎯 Complete setup and deployment in one go!\n")
    
    config = Config(project_path)
    
    # Step 1: Check if configuration exists
    if config.exists():
        info("📋 Configuration found")
        
        # Ask if user wants to reconfigure
        reconfigure = questionary.confirm(
            "Configuration already exists. Do you want to reconfigure?",
            default=False
        ).ask()
        
        if reconfigure:
            if not _run_init(project_path):
                return False
        else:
            info("Using existing configuration")
    else:
        info("📋 No configuration found - starting setup")
        if not _run_init(project_path):
            return False
    
    # Step 2: Deploy with retry loop
    info("🚀 Starting deployment process")
    
    max_attempts = 3
    attempt = 1
    
    while attempt <= max_attempts:
        if attempt > 1:
            print(f"\n🔄 Deployment attempt {attempt}/{max_attempts}")
        
        success_deploy = _run_deploy(project_path)
        
        if success_deploy:
            success("🎉 Interactive deployment completed successfully!")
            _show_completion_message()
            return True
        
        # Deployment failed
        if attempt < max_attempts:
            warning(f"❌ Deployment attempt {attempt} failed")
            
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
                attempt += 1
                continue
            elif choice == "Reconfigure and retry":
                info("🔧 Reconfiguring...")
                if not _run_init(project_path):
                    return False
                attempt += 1
                continue
            else:
                error("Deployment cancelled by user")
                return False
        else:
            error(f"❌ All {max_attempts} deployment attempts failed")
            _show_failure_help()
            return False
    
    return False

def _run_init(project_path: str) -> bool:
    """Run initialization with error handling"""
    try:
        info("🔧 Running initialization...")
        return init_command(project_path)
    except Exception as e:
        error(f"❌ Initialization failed: {str(e)}")
        return False

def _run_deploy(project_path: str) -> bool:
    """Run deployment with error handling"""
    try:
        info("🚀 Running deployment...")
        return deploy_command(project_path)
    except Exception as e:
        error(f"❌ Deployment failed: {str(e)}")
        return False

def _show_completion_message() -> None:
    """Show completion message with next steps"""
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
    """Show help message when all attempts fail"""
    print("\n🔧 Troubleshooting Help:")
    print("   • Check your internet connection")
    print("   • Verify your GitHub token is valid")
    print("   • Ensure repository exists and you have write access")
    print("   • Try running 'deployx init' and 'deployx deploy' separately")
    print("   • Use 'deployx --verbose deploy' for detailed error information")
    print("\n📞 Need help? Check the documentation or open an issue")