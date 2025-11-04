"""
Build management utilities.
"""
import subprocess
from typing import Tuple
from pathlib import Path
from core.logging import get_logger

class BuildManager:
    """Manages build processes."""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.logger = get_logger(__name__)
    
    def execute_build(self, build_command: str, output_dir: str) -> Tuple[bool, str]:
        """Execute build command."""
        try:
            result = subprocess.run(
                build_command.split(),
                cwd=self.project_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return True, "Build successful"
            else:
                return False, f"Build failed: {result.stderr}"
                
        except Exception as e:
            return False, f"Build error: {str(e)}"
