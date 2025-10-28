"""
Logs viewing commands for DeployX.

Provides commands to view and stream deployment logs from platforms.
Note: Log support varies by platform - some platforms may not provide logs.

Example:
    >>> from commands.logs import logs_command
    >>> logs_command("./my-project", follow=True)
"""

from typing import Optional
from utils.ui import error, info, warning
from utils.config import Config
from platforms.factory import get_platform


def logs_command(project_path: str = ".", follow: bool = False, 
                tail: Optional[int] = None) -> bool:
    """
    View deployment logs from configured platform.
    
    Fetches and displays logs from the deployment platform.
    Can show static logs or stream in real-time.
    
    Args:
        project_path: Path to project directory (default: current directory)
        follow: Stream logs in real-time (default: False)
        tail: Number of lines to show from end (default: all)
    
    Returns:
        True if successful, False otherwise
    
    Example:
        >>> logs_command("./my-app", follow=True)
        True
    """
    config = Config(project_path)
    
    if not config.exists():
        error("❌ No configuration found. Run 'deployx init' first.")
        return False
    
    try:
        config_data = config.load()
        platform_name = config_data.get('platform')
        
        if not platform_name:
            error("❌ No platform configured")
            return False
        
        # Get platform instance
        platform = get_platform(platform_name, config_data)
        
        if follow:
            info("📡 Streaming logs (Press Ctrl+C to stop)...")
            return _stream_logs(platform)
        else:
            info("📋 Fetching deployment logs...")
            return _fetch_logs(platform, tail)
            
    except Exception as e:
        error(f"❌ Failed to fetch logs: {str(e)}")
        return False


def _fetch_logs(platform, tail: Optional[int] = None) -> bool:
    """
    Fetch static logs from platform.
    
    Retrieves logs and displays them. Shows warning if platform
    doesn't support logs yet.
    
    Args:
        platform: Platform instance
        tail: Number of lines to show from end
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if platform supports logs
        if not hasattr(platform, 'get_logs'):
            warning("⚠️  Logs not supported for this platform yet")
            info("💡 This feature will be added in future updates")
            return True
        
        logs = platform.get_logs(tail=tail)
        
        if not logs:
            warning("📋 No logs available")
            return True
        
        # Display logs
        for log_line in logs:
            print(log_line)
        
        return True
        
    except Exception as e:
        error(f"❌ Failed to fetch logs: {str(e)}")
        return False


def _stream_logs(platform) -> bool:
    """
    Stream logs in real-time from platform.
    
    Continuously streams logs until interrupted by user (Ctrl+C).
    Shows warning if platform doesn't support streaming.
    
    Args:
        platform: Platform instance
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not hasattr(platform, 'stream_logs'):
            warning("⚠️  Real-time logs not supported for this platform yet")
            info("💡 This feature will be added in future updates")
            return True
        
        # Stream logs until interrupted
        for log_line in platform.stream_logs():
            print(log_line)
            
    except KeyboardInterrupt:
        info("\n📡 Log streaming stopped")
        return True
    except Exception as e:
        error(f"❌ Log streaming failed: {str(e)}")
        return False
