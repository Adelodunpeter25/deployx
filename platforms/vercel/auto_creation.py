"""
Vercel project auto-creation functionality.
"""
import os
from typing import Tuple, Optional
from pathlib import Path
from core.logging import get_logger
from .api_integration import VercelAPIIntegration
from .cli_integration import VercelCLIIntegration

class VercelAutoCreation:
    """Handles automatic Vercel project creation and setup."""
    
    def __init__(self, token: str, use_cli: bool = True):
        self.token = token
        self.use_cli = use_cli
        self.logger = get_logger(__name__)
        
        if use_cli:
            self.cli_integration = VercelCLIIntegration()
        
        if token:
            self.api_integration = VercelAPIIntegration(token)
        else:
            self.api_integration = None
    
    def should_create_project(self, project_path: str = ".") -> Tuple[bool, str]:
        """
        Determine if we should auto-create a Vercel project.
        
        Returns:
            Tuple of (should_create, reason)
        """
        # Check for existing Vercel configuration
        vercel_config = Path(project_path) / '.vercel'
        if vercel_config.exists():
            return False, "Vercel project already configured"
        
        # Check for vercel.json
        vercel_json = Path(project_path) / 'vercel.json'
        if vercel_json.exists():
            return False, "vercel.json found, project may already exist"
        
        return True, "No Vercel project detected"
    
    def auto_create_project(self, project_name: str, project_path: str = ".", framework: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Auto-create Vercel project and configure it.
        
        Returns:
            Tuple of (success, message, project_url)
        """
        try:
            # Check if we should create
            should_create, reason = self.should_create_project(project_path)
            if not should_create:
                self.logger.info(f"Skipping project creation: {reason}")
                return True, reason, None
            
            # Get suggested project name
            suggested_name = self._generate_suggested_name(project_name)
            
            # Prompt user for project name
            final_name = self._prompt_for_project_name(suggested_name)
            if not final_name:
                return False, "Project creation cancelled", None
            
            # Try CLI first if available
            if self.use_cli and self.cli_integration.is_cli_available():
                return self._create_via_cli(final_name, project_path)
            
            # Fallback to API
            elif self.api_integration:
                return self._create_via_api(final_name, framework)
            
            else:
                return False, "No authentication method available", None
                
        except Exception as e:
            return False, f"Failed to create project: {str(e)}", None
    
    def _generate_suggested_name(self, project_name: str) -> str:
        """Generate a suggested project name."""
        # Clean up project name
        suggested = project_name.lower().replace(" ", "-").replace("_", "-")
        # Remove invalid characters
        suggested = "".join(c for c in suggested if c.isalnum() or c == "-")
        return suggested
    
    def _prompt_for_project_name(self, suggested_name: str) -> Optional[str]:
        """Prompt user for project name with suggestion."""
        try:
            print(f"\n📁 Vercel project name: {suggested_name}")
            user_input = input("   Use default (press Enter) or enter custom name: ").strip()
            
            if not user_input:
                return suggested_name
            
            # Clean custom name
            custom_name = user_input.lower().replace(" ", "-").replace("_", "-")
            custom_name = "".join(c for c in custom_name if c.isalnum() or c == "-")
            return custom_name
            
        except KeyboardInterrupt:
            print("\n❌ Project creation cancelled")
            return None
    
    def _create_via_cli(self, project_name: str, project_path: str) -> Tuple[bool, str, Optional[str]]:
        """Create project using Vercel CLI."""
        success, message = self.cli_integration.create_project(project_name, project_path)
        
        if success:
            # Generate project URL
            user = self.cli_integration.get_authenticated_user()
            project_url = f"https://{project_name}.vercel.app" if user else None
            return True, message, project_url
        else:
            return False, message, None
    
    def _create_via_api(self, project_name: str, framework: Optional[str]) -> Tuple[bool, str, Optional[str]]:
        """Create project using Vercel API."""
        success, message, project_id = self.api_integration.create_project(project_name, framework)
        
        if success:
            project_url = f"https://{project_name}.vercel.app"
            return True, message, project_url
        else:
            return False, message, None
