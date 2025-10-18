import yaml
from pathlib import Path
from typing import Dict, Any

CONFIG_FILE = "deployx.yml"

class Config:
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.config_path = self.project_path / CONFIG_FILE
        self._data = {}
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from deployx.yml"""
        if not self.config_path.exists():
            return {}
        
        with open(self.config_path, 'r') as f:
            self._data = yaml.safe_load(f) or {}
        return self._data
    
    def save(self, data: Dict[str, Any]) -> None:
        """Save configuration to deployx.yml"""
        self._data = data
        with open(self.config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, indent=2)
    
    def exists(self) -> bool:
        """Check if config file exists"""
        return self.config_path.exists()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        if not self._data:
            self.load()
        return self._data.get(key, default)
    
    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        """Get platform-specific configuration"""
        return self.get(platform, {})

def create_default_config(project_name: str, project_type: str, platform: str) -> Dict[str, Any]:
    """Create default configuration structure"""
    return {
        "project": {
            "name": project_name,
            "type": project_type
        },
        "build": {
            "command": "npm run build" if project_type == "react" else None,
            "output": "build" if project_type == "react" else "."
        },
        "platform": platform,
        platform: {}
    }