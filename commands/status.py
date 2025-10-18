from typing import Optional
from datetime import datetime

from utils.ui import header, success, error, info
from utils.config import Config
from platforms.factory import get_platform

def status_command(project_path: str = ".") -> bool:
    """Check deployment status for configured platform"""
    
    config = Config(project_path)
    
    # Check if configuration exists
    if not config.exists():
        error("❌ No configuration found")
        print("   Run 'deployx init' first to set up deployment")
        return False
    
    # Load configuration
    try:
        config_data = config.load()
    except Exception as e:
        error(f"❌ Failed to load configuration: {str(e)}")
        return False
    
    platform_name = config_data.get('platform')
    if not platform_name:
        error("❌ No platform configured")
        return False
    
    # Get platform instance
    platform_config = config_data.get(platform_name, {})
    
    try:
        platform = get_platform(platform_name, platform_config)
    except Exception as e:
        error(f"❌ Failed to initialize {platform_name} platform: {str(e)}")
        return False
    
    # Display header
    header(f"Deployment Status - {platform_name.title()}")
    
    # Validate credentials first
    info("🔐 Checking authentication...")
    valid, auth_message = platform.validate_credentials()
    
    if not valid:
        error(f"❌ Authentication failed: {auth_message}")
        _show_auth_troubleshooting(platform_name)
        return False
    
    success("✅ Authentication successful")
    
    # Fetch deployment status
    info("📊 Fetching deployment status...")
    
    try:
        status = platform.get_status()
    except Exception as e:
        error(f"❌ Failed to fetch status: {str(e)}")
        return False
    
    # Display status information
    _display_status_info(config_data, status, platform)
    
    # Show troubleshooting if needed
    if status.status in ['error', 'unknown']:
        _show_status_troubleshooting(status, platform_name)
    
    return True

def _display_status_info(config_data: dict, status, platform) -> None:
    """Display formatted status information"""
    project = config_data.get('project', {})
    platform_name = config_data.get('platform')
    platform_config = config_data.get(platform_name, {})
    
    print("\n📋 Project Information:")
    print(f"   Project: {project.get('name', 'Unknown')}")
    print(f"   Type: {project.get('type', 'Unknown')}")
    print(f"   Platform: {platform_name}")
    
    if platform_name == 'github':
        print(f"   Repository: {platform_config.get('repo', 'Not configured')}")
        print(f"   Branch: {platform_config.get('branch', 'gh-pages')}")
        print(f"   Method: {platform_config.get('method', 'branch')}")
    
    print("\n🚀 Deployment Status:")
    
    # Status with appropriate icon and color
    status_display = _format_status(status.status)
    print(f"   Status: {status_display}")
    
    # Live URL
    if status.url:
        print(f"   Live URL: {status.url}")
    elif platform.get_url():
        print(f"   Expected URL: {platform.get_url()}")
    else:
        print("   URL: Not available")
    
    # Last updated
    if status.last_updated:
        try:
            # Parse ISO format datetime
            dt = datetime.fromisoformat(status.last_updated.replace('Z', '+00:00'))
            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            print(f"   Last Updated: {formatted_time}")
        except:
            print(f"   Last Updated: {status.last_updated}")
    else:
        print("   Last Updated: Unknown")
    
    # Status message
    if status.message:
        print(f"   Details: {status.message}")
    
    # Additional platform-specific info
    if platform_name == 'github':
        _display_github_specific_info(platform_config)

def _format_status(status: str) -> str:
    """Format status with appropriate icon and description"""
    status_map = {
        'ready': '🟢 Ready (Live)',
        'building': '🟡 Building (In Progress)', 
        'error': '🔴 Error (Failed)',
        'unknown': '⚪ Unknown (Not Configured)'
    }
    
    return status_map.get(status, f"❓ {status.title()}")

def _display_github_specific_info(platform_config: dict) -> None:
    """Display GitHub-specific status information"""
    print("\n🐙 GitHub Pages Info:")
    
    method = platform_config.get('method', 'branch')
    if method == 'branch':
        branch = platform_config.get('branch', 'gh-pages')
        print(f"   Source: {branch} branch")
        print(f"   💡 Files are served from the {branch} branch root")
    else:
        print("   Source: docs/ folder (main branch)")
        print("   💡 Files are served from the docs/ folder")
    
    print("   🔗 GitHub Pages may take 1-10 minutes to update after deployment")

def _show_auth_troubleshooting(platform_name: str) -> None:
    """Show authentication troubleshooting tips"""
    print("\n🔧 Authentication Troubleshooting:")
    
    if platform_name == 'github':
        print("   • Check your GitHub personal access token")
        print("   • Ensure token has 'repo' and 'workflow' permissions")
        print("   • Verify .deployx_token file exists and contains valid token")
        print("   • Token may have expired - run 'deployx init' to update")
        print("   • Check repository exists and you have write access")

def _show_status_troubleshooting(status, platform_name: str) -> None:
    """Show status-specific troubleshooting tips"""
    print("\n🔧 Troubleshooting Tips:")
    
    if status.status == 'error':
        print("   • Check the deployment logs in your platform dashboard")
        print("   • Verify your build command works locally")
        print("   • Ensure output directory contains valid files")
        print("   • Try running 'deployx deploy' again")
        
        if platform_name == 'github':
            print("   • Check GitHub Actions tab for detailed error logs")
            print("   • Verify GitHub Pages is enabled in repository settings")
    
    elif status.status == 'unknown':
        print("   • Deployment may not be configured yet")
        print("   • Run 'deployx deploy' to create initial deployment")
        
        if platform_name == 'github':
            print("   • Check if GitHub Pages is enabled in repository settings")
            print("   • Verify the target branch exists")
    
    elif status.status == 'building':
        print("   • Deployment is in progress, please wait")
        print("   • Large sites may take several minutes to build")
        print("   • Run this command again in a few minutes")

def quick_status_command(project_path: str = ".") -> Optional[str]:
    """Get quick status for CI/CD (returns just the status string)"""
    config = Config(project_path)
    
    if not config.exists():
        return None
    
    try:
        config_data = config.load()
        platform_name = config_data.get('platform')
        platform_config = config_data.get(platform_name, {})
        
        platform = get_platform(platform_name, platform_config)
        
        # Quick validation
        valid, _ = platform.validate_credentials()
        if not valid:
            return 'auth_failed'
        
        status = platform.get_status()
        return status.status
        
    except Exception:
        return 'error'