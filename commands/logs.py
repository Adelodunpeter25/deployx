"""
Logs viewing commands for DeployX
"""

import time
from typing import Optional, List
from utils.ui import header, success, error, info, warning
from utils.config import Config
from platforms.factory import get_platform

def logs_command(project_path: str = ".", follow: bool = False, tail: Optional[int] = None) -> bool:
    """View deployment logs"""
    
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
    """Fetch static logs"""
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
        
        for log_line in logs:
            print(log_line)
        
        return True
        
    except Exception as e:
        error(f"❌ Failed to fetch logs: {str(e)}")
        return False

def _stream_logs(platform) -> bool:
    """Stream logs in real-time"""
    try:
        if not hasattr(platform, 'stream_logs'):
            warning("⚠️  Real-time logs not supported for this platform yet")
            info("💡 This feature will be added in future updates")
            return True
        
        for log_line in platform.stream_logs():
            print(log_line)
            
    except KeyboardInterrupt:
        info("\n📡 Log streaming stopped")
        return True
    except Exception as e:
        error(f"❌ Log streaming failed: {str(e)}")
        return False