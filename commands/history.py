"""
Deployment history commands for DeployX
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.ui import header, success, error, info, warning
from utils.config import Config

def history_command(project_path: str = ".", limit: Optional[int] = None) -> bool:
    """Show deployment history"""
    
    config = Config(project_path)
    
    if not config.exists():
        error("❌ No configuration found. Run 'deployx init' first.")
        return False
    
    try:
        history = _load_history(project_path)
        
        if not history:
            warning("📋 No deployment history found")
            info("💡 History will be recorded after your first deployment")
            return True
        
        # Apply limit if specified
        if limit:
            history = history[-limit:]
        
        header("Deployment History")
        
        for i, deployment in enumerate(reversed(history), 1):
            _display_deployment(deployment, i)
        
        info(f"📊 Showing {len(history)} deployment(s)")
        return True
        
    except Exception as e:
        error(f"❌ Failed to load history: {str(e)}")
        return False

def add_to_history(project_path: str, deployment_data: Dict[str, Any]) -> None:
    """Add deployment to history"""
    try:
        history = _load_history(project_path)
        
        # Add timestamp if not present
        if 'timestamp' not in deployment_data:
            deployment_data['timestamp'] = datetime.now().isoformat()
        
        history.append(deployment_data)
        
        # Keep only last 50 deployments
        if len(history) > 50:
            history = history[-50:]
        
        _save_history(project_path, history)
        
        # Add to .gitignore
        _add_to_gitignore(project_path)
        
    except Exception:
        # Don't fail deployment if history fails
        pass

def _load_history(project_path: str) -> List[Dict[str, Any]]:
    """Load deployment history from file"""
    history_file = Path(project_path) / ".deployx_history.json"
    
    if not history_file.exists():
        return []
    
    try:
        with open(history_file, 'r') as f:
            return json.load(f)
    except:
        return []

def _save_history(project_path: str, history: List[Dict[str, Any]]) -> None:
    """Save deployment history to file"""
    history_file = Path(project_path) / ".deployx_history.json"
    
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)

def _add_to_gitignore(project_path: str) -> None:
    """Add history file to .gitignore"""
    try:
        gitignore_path = Path(project_path) / ".gitignore"
        history_entry = ".deployx_history.json"
        
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                content = f.read()
            if history_entry not in content:
                with open(gitignore_path, 'a') as f:
                    f.write(f'\n{history_entry}\n')
        else:
            with open(gitignore_path, 'w') as f:
                f.write(f'{history_entry}\n')
    except:
        pass

def _display_deployment(deployment: Dict[str, Any], index: int) -> None:
    """Display a single deployment entry"""
    timestamp = deployment.get('timestamp', 'Unknown')
    platform = deployment.get('platform', 'Unknown')
    status = deployment.get('status', 'Unknown')
    url = deployment.get('url')
    commit = deployment.get('commit_id', '')
    deploy_time = deployment.get('deploy_time')
    
    # Format timestamp
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        formatted_time = timestamp
    
    # Status emoji
    status_emoji = {
        'success': '✅',
        'failed': '❌', 
        'building': '🔄',
        'ready': '✅'
    }.get(status.lower(), '❓')
    
    print(f"\n{index}. {status_emoji} {formatted_time}")
    print(f"   Platform: {platform}")
    print(f"   Status: {status}")
    if commit:
        print(f"   Commit: {commit[:7]}")
    if url:
        print(f"   URL: {url}")
    if deploy_time:
        print(f"   Duration: {deploy_time:.1f}s")
    
    # Add separator
    print("   " + "─" * 40)