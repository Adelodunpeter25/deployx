"""
Authentication management commands for DeployX.
"""
import os
import webbrowser
from pathlib import Path
from typing import Dict, Optional
from utils.ui import header, success, error, info, warning
from platforms.github.cli_integration import GitHubCLIIntegration
from platforms.vercel.cli_integration import VercelCLIIntegration
from platforms.railway.cli_integration import RailwayCLIIntegration

def auth_status_command() -> bool:
    """Show authentication status for all platforms."""
    header("Authentication Status")
    
    platforms = {
        "GitHub": _check_github_auth(),
        "Vercel": _check_vercel_auth(),
        "Railway": _check_railway_auth(),
        "Netlify": _check_netlify_auth(),
        "Render": _check_render_auth()
    }
    
    for platform, (status, method, user) in platforms.items():
        if status:
            success(f"✅ {platform}: Connected via {method}" + (f" ({user})" if user else ""))
        else:
            error(f"❌ {platform}: Not configured")
            info(f"   Run: deployx auth setup {platform.lower()}")
    
    return True

def auth_setup_command(platform: str) -> bool:
    """Set up authentication for a specific platform."""
    platform = platform.lower()
    
    if platform not in ["github", "vercel", "railway", "netlify", "render"]:
        error(f"❌ Unknown platform: {platform}")
        return False
    
    header(f"Setting up {platform.title()} Authentication")
    
    # Check if already configured
    status_func = {
        "github": _check_github_auth,
        "vercel": _check_vercel_auth,
        "railway": _check_railway_auth,
        "netlify": _check_netlify_auth,
        "render": _check_render_auth
    }[platform]
    
    is_configured, method, user = status_func()
    if is_configured:
        warning(f"⚠️ {platform.title()} is already configured via {method}" + (f" ({user})" if user else ""))
        reconfigure = input("Do you want to reconfigure? (y/N): ").strip().lower()
        if reconfigure not in ['y', 'yes']:
            return True
    
    # Open token page and guide setup
    return _setup_platform_auth(platform)

def auth_clear_command(platform: str) -> bool:
    """Clear stored authentication for a platform."""
    platform = platform.lower()
    
    if platform not in ["github", "vercel", "railway", "netlify", "render"]:
        error(f"❌ Unknown platform: {platform}")
        return False
    
    # Remove token file
    token_file = Path(f'.deployx_{platform}_token')
    if token_file.exists():
        try:
            token_file.unlink()
            success(f"✅ Cleared {platform.title()} authentication")
        except Exception as e:
            error(f"❌ Failed to clear token: {e}")
            return False
    else:
        warning(f"⚠️ No stored token found for {platform.title()}")
    
    return True

def _check_github_auth() -> tuple[bool, str, Optional[str]]:
    """Check GitHub authentication status."""
    cli = GitHubCLIIntegration()
    
    # Check CLI first
    if cli.is_cli_available():
        user = cli.get_authenticated_user()
        return True, "CLI", user
    
    # Check token file
    token_file = Path('.deployx_github_token')
    if token_file.exists():
        return True, "token file", None
    
    # Check environment
    if os.getenv('GITHUB_TOKEN'):
        return True, "environment", None
    
    return False, "", None

def _check_vercel_auth() -> tuple[bool, str, Optional[str]]:
    """Check Vercel authentication status."""
    cli = VercelCLIIntegration()
    
    # Check CLI first
    if cli.is_cli_available():
        user = cli.get_authenticated_user()
        return True, "CLI", user
    
    # Check token file
    token_file = Path('.deployx_vercel_token')
    if token_file.exists():
        return True, "token file", None
    
    # Check environment
    if os.getenv('VERCEL_TOKEN'):
        return True, "environment", None
    
    return False, "", None

def _check_railway_auth() -> tuple[bool, str, Optional[str]]:
    """Check Railway authentication status."""
    cli = RailwayCLIIntegration()
    
    # Check CLI first
    if cli.is_cli_available():
        user = cli.get_authenticated_user()
        return True, "CLI", user
    
    # Check token file
    token_file = Path('.deployx_railway_token')
    if token_file.exists():
        return True, "token file", None
    
    # Check environment
    if os.getenv('RAILWAY_TOKEN'):
        return True, "environment", None
    
    return False, "", None

def _check_netlify_auth() -> tuple[bool, str, Optional[str]]:
    """Check Netlify authentication status."""
    # Check token file
    token_file = Path('.deployx_netlify_token')
    if token_file.exists():
        return True, "token file", None
    
    # Check environment
    if os.getenv('NETLIFY_TOKEN'):
        return True, "environment", None
    
    return False, "", None

def _check_render_auth() -> tuple[bool, str, Optional[str]]:
    """Check Render authentication status."""
    # Check token file
    token_file = Path('.deployx_render_token')
    if token_file.exists():
        return True, "token file", None
    
    # Check environment
    if os.getenv('RENDER_TOKEN'):
        return True, "environment", None
    
    return False, "", None

def _setup_platform_auth(platform: str) -> bool:
    """Set up authentication for a platform with guided flow."""
    token_urls = {
        "github": "https://github.com/settings/tokens/new?scopes=repo,workflow&description=DeployX%20CLI",
        "vercel": "https://vercel.com/account/tokens",
        "railway": "https://railway.app/account/tokens",
        "netlify": "https://app.netlify.com/user/applications#personal-access-tokens",
        "render": "https://dashboard.render.com/account/api-keys"
    }
    
    instructions = {
        "github": "Create a token with 'repo' and 'workflow' scopes",
        "vercel": "Create a new token for DeployX CLI",
        "railway": "Create a new token for DeployX CLI", 
        "netlify": "Create a new personal access token",
        "render": "Create a new API key"
    }
    
    try:
        info(f"🎯 Setting up {platform.title()} authentication")
        info(f"📝 {instructions[platform]}")
        
        # Ask if user wants to open the page
        open_page = input(f"🔗 Open {platform.title()} token page? (Y/n): ").strip().lower()
        if open_page not in ['n', 'no']:
            webbrowser.open(token_urls[platform])
            info(f"✅ Opened {platform.title()} token page in browser")
        
        # Get token from user
        token = input(f"📋 Paste your {platform.title()} token: ").strip()
        
        if not token:
            error("❌ No token provided")
            return False
        
        # Save token
        token_file = Path(f'.deployx_{platform}_token')
        try:
            with open(token_file, 'w') as f:
                f.write(token)
            success(f"✅ {platform.title()} token saved")
        except Exception as e:
            error(f"❌ Failed to save token: {e}")
            return False
        
        # Test token
        info(f"🔐 Testing {platform.title()} connection...")
        if _test_platform_token(platform, token):
            success(f"✅ {platform.title()} configured successfully!")
            return True
        else:
            error(f"❌ Token validation failed")
            # Remove invalid token
            token_file.unlink(missing_ok=True)
            return False
            
    except KeyboardInterrupt:
        error(f"\n❌ {platform.title()} setup cancelled")
        return False

def _test_platform_token(platform: str, token: str) -> bool:
    """Test if a platform token is valid."""
    try:
        if platform == "github":
            from platforms.github.platform import GitHubPlatform
            config = {'github': {}}
            platform_instance = GitHubPlatform(config)
            valid, _ = platform_instance.validate_credentials()
            return valid
        
        elif platform == "vercel":
            from platforms.vercel.platform import VercelPlatform
            config = {'vercel': {}}
            platform_instance = VercelPlatform(config)
            valid, _ = platform_instance.validate_credentials()
            return valid
        
        elif platform == "railway":
            from platforms.railway.platform import RailwayPlatform
            config = {'railway': {}}
            platform_instance = RailwayPlatform(config)
            valid, _ = platform_instance.validate_credentials()
            return valid
        
        elif platform == "netlify":
            # Test Netlify token by calling user API
            import requests
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get("https://api.netlify.com/api/v1/user", headers=headers)
            return response.status_code == 200
        
        elif platform == "render":
            # Test Render token by calling user API
            import requests
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get("https://api.render.com/v1/owners", headers=headers)
            return response.status_code == 200
        
        return False
        
    except Exception:
        return False
