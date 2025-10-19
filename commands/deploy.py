import time
import webbrowser
from typing import Optional
import questionary

from utils.ui import header, success, error, info, warning, spinner, print_url
from utils.config import Config
from utils.validator import validate_config
from platforms.factory import get_platform

def deploy_command(project_path: str = ".", dry_run: bool = False) -> bool:
    """Execute deployment to configured platform"""
    
    config = Config(project_path)
    
    # Check if configuration exists
    if not config.exists():
        error("❌ No configuration found")
        print("   Run 'deployx init' first to set up deployment")
        return False
    
    # Load and validate configuration
    try:
        config_data = config.load()
        errors = validate_config(config_data)
        
        if errors:
            error("❌ Configuration validation failed:")
            for err in errors:
                print(f"   • {err}")
            print("   Run 'deployx init' to fix configuration")
            return False
            
    except Exception as e:
        error(f"❌ Failed to load configuration: {str(e)}")
        return False
    
    # Handle dry-run mode
    if dry_run:
        return _show_dry_run_summary(config_data)
    
    # Display deployment summary
    if not _show_deployment_summary(config_data):
        info("Deployment cancelled")
        return False
    
    # Get platform instance
    platform_name = config_data.get('platform')
    platform_config = config_data.get(platform_name, {})
    
    try:
        platform = get_platform(platform_name, platform_config)
    except Exception as e:
        error(f"❌ Failed to initialize {platform_name} platform: {str(e)}")
        return False
    
    # Start deployment process
    header(f"Deploying to {platform_name.title()}")
    start_time = time.time()
    
    # Step 1: Validate credentials
    info("🔐 Validating credentials...")
    with spinner("Checking authentication"):
        valid, message = platform.validate_credentials()
    
    if not valid:
        error(f"❌ Credential validation failed: {message}")
        return False
    
    success(f"✅ {message}")
    
    # Step 2: Prepare deployment
    build_config = config_data.get('build', {})
    build_command = build_config.get('command')
    output_dir = build_config.get('output', '.')
    
    info("🔨 Preparing deployment...")
    
    if build_command:
        with spinner(f"Running build command: {build_command}"):
            prepared, prep_message = platform.prepare_deployment(
                project_path, build_command, output_dir
            )
    else:
        with spinner("Checking files"):
            prepared, prep_message = platform.prepare_deployment(
                project_path, None, output_dir
            )
    
    if not prepared:
        error(f"❌ Preparation failed: {prep_message}")
        return False
    
    success(f"✅ {prep_message}")
    
    # Step 3: Execute deployment
    info("🚀 Executing deployment...")
    
    with spinner("Deploying to platform"):
        result = platform.execute_deployment(project_path, output_dir)
    
    if not result.success:
        error(f"❌ Deployment failed: {result.message}")
        return False
    
    # Calculate deployment time
    deploy_time = time.time() - start_time
    
    # Step 4: Display success results
    success("🎉 Deployment successful!")
    
    if result.url:
        print_url("🌐 Live URL", result.url)
    
    if result.deployment_id:
        info(f"📋 Deployment ID: {result.deployment_id}")
    
    info(f"⏱️  Deployment completed in {deploy_time:.1f} seconds")
    
    # Step 5: Offer to open URL
    if result.url:
        open_browser = questionary.confirm(
            "🌍 Open deployment URL in browser?",
            default=False
        ).ask()
        
        if open_browser:
            try:
                webbrowser.open(result.url)
                success("🌍 Opened in browser")
            except Exception as e:
                warning(f"Could not open browser: {str(e)}")
    
    # Record deployment in history
    try:
        from commands.history import add_to_history
        from git import Repo
        
        # Try to get commit ID
        commit_id = None
        try:
            repo = Repo(project_path)
            commit_id = repo.head.commit.hexsha
        except:
            pass
        
        add_to_history(project_path, {
            'platform': platform_name,
            'status': 'success',
            'url': result.url,
            'deployment_id': result.deployment_id,
            'commit_id': commit_id,
            'deploy_time': deploy_time
        })
    except:
        # Don't fail deployment if history recording fails
        pass
    
    # Show next steps
    _show_post_deployment_info(platform_name, result.url)
    
    return True

def _show_deployment_summary(config_data: dict) -> bool:
    """Display deployment summary and get confirmation"""
    project = config_data.get('project', {})
    build = config_data.get('build', {})
    platform_name = config_data.get('platform')
    platform_config = config_data.get(platform_name, {})
    
    print("\n📋 Deployment Summary:")
    print(f"   Project: {project.get('name', 'Unknown')}")
    print(f"   Type: {project.get('type', 'Unknown')}")
    print(f"   Platform: {platform_name}")
    
    if platform_name == 'github':
        print(f"   Repository: {platform_config.get('repo', 'Not configured')}")
        print(f"   Method: {platform_config.get('method', 'branch')}")
        if platform_config.get('method') == 'branch':
            print(f"   Branch: {platform_config.get('branch', 'gh-pages')}")
    
    if build.get('command'):
        print(f"   Build: {build.get('command')}")
    
    print(f"   Output: {build.get('output', '.')}")
    
    print("\n⚠️  This will:")
    if platform_name == 'github':
        method = platform_config.get('method', 'branch')
        if method == 'branch':
            print(f"   • Push files to {platform_config.get('branch', 'gh-pages')} branch")
        else:
            print("   • Update docs/ folder in main branch")
        print("   • Overwrite existing deployment")
        print("   • Make your site publicly accessible")
    
    return questionary.confirm(
        "\n🚀 Proceed with deployment?",
        default=True
    ).ask()

def _show_post_deployment_info(platform_name: str, url: Optional[str]) -> None:
    """Show information after successful deployment"""
    print("\n💡 What's next:")
    print("   • Your site is now live and publicly accessible")
    
    if platform_name == 'github':
        print("   • GitHub Pages may take a few minutes to update")
        print("   • Check GitHub repository settings for Pages configuration")
    
    print("   • Run 'deployx status' to check deployment status")
    print("   • Run 'deployx deploy' again to update your site")
    
    if url:
        print(f"   • Bookmark your site: {url}")

def _show_dry_run_summary(config_data: dict) -> bool:
    """Show what would happen in a deployment without actually deploying"""
    project = config_data.get('project', {})
    build = config_data.get('build', {})
    platform_name = config_data.get('platform')
    platform_config = config_data.get(platform_name, {})
    
    header("Dry Run - Deployment Preview")
    
    print("\n📄 Configuration:")
    print(f"   Project: {project.get('name', 'Unknown')}")
    print(f"   Type: {project.get('type', 'Unknown')}")
    print(f"   Platform: {platform_name}")
    
    if platform_name == 'github':
        print(f"   Repository: {platform_config.get('repo', 'Not configured')}")
        print(f"   Method: {platform_config.get('method', 'branch')}")
        if platform_config.get('method') == 'branch':
            print(f"   Branch: {platform_config.get('branch', 'gh-pages')}")
    elif platform_name in ['vercel', 'netlify', 'railway', 'render']:
        if platform_config.get('name'):
            print(f"   Service: {platform_config.get('name')}")
    
    print("\n🔨 Build Process:")
    if build.get('command'):
        print(f"   • Run build command: {build.get('command')}")
    else:
        print("   • No build command configured")
    
    print(f"   • Deploy from: {build.get('output', '.')}")
    
    print("\n🚀 Deployment Steps:")
    print("   1. Validate credentials")
    print("   2. Run build process (if configured)")
    print("   3. Prepare deployment files")
    print("   4. Upload to platform")
    print("   5. Update live site")
    
    print("\nℹ️  This is a dry run - no actual deployment will occur")
    print("   Run 'deployx deploy' to perform the actual deployment")
    
    return True

def redeploy_command(project_path: str = ".") -> bool:
    """Quick redeploy without confirmation (for CI/CD)"""
    config = Config(project_path)
    
    if not config.exists():
        error("❌ No configuration found. Run 'deployx init' first.")
        return False
    
    # Load configuration
    config_data = config.load()
    platform_name = config_data.get('platform')
    platform_config = config_data.get(platform_name, {})
    
    try:
        platform = get_platform(platform_name, platform_config)
    except Exception as e:
        error(f"❌ Platform initialization failed: {str(e)}")
        return False
    
    # Quick deployment without prompts
    header(f"Redeploying to {platform_name.title()}")
    
    # Validate credentials
    valid, message = platform.validate_credentials()
    if not valid:
        error(f"❌ Authentication failed: {message}")
        return False
    
    # Prepare and deploy
    build_config = config_data.get('build', {})
    prepared, prep_message = platform.prepare_deployment(
        project_path, 
        build_config.get('command'), 
        build_config.get('output', '.')
    )
    
    if not prepared:
        error(f"❌ Preparation failed: {prep_message}")
        return False
    
    result = platform.execute_deployment(
        project_path, 
        build_config.get('output', '.')
    )
    
    if result.success:
        success(f"🎉 Redeployment successful: {result.url}")
        return True
    else:
        error(f"❌ Redeployment failed: {result.message}")
        return False