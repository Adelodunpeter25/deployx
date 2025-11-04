"""
Railway project and service auto-creation functionality.
"""
import os
from typing import Tuple, Optional, Dict, Any
from pathlib import Path
from core.logging import get_logger
from .api_integration import RailwayAPIIntegration
from .cli_integration import RailwayCLIIntegration

class RailwayAutoCreation:
    """Handles automatic Railway project and service creation."""
    
    def __init__(self, token: str, use_cli: bool = True):
        self.token = token
        self.use_cli = use_cli
        self.logger = get_logger(__name__)
        
        if use_cli:
            self.cli_integration = RailwayCLIIntegration()
        
        if token:
            self.api_integration = RailwayAPIIntegration(token)
        else:
            self.api_integration = None
    
    def should_create_project(self, project_path: str = ".") -> Tuple[bool, str]:
        """
        Determine if we should auto-create a Railway project.
        
        Returns:
            Tuple of (should_create, reason)
        """
        # Check for existing Railway configuration
        railway_config = Path(project_path) / '.railway'
        if railway_config.exists():
            return False, "Railway project already configured"
        
        # Check for railway.json
        railway_json = Path(project_path) / 'railway.json'
        if railway_json.exists():
            return False, "railway.json found, project may already exist"
        
        return True, "No Railway project detected"
    
    def auto_create_complete_setup(self, project_name: str, project_path: str = ".", service_name: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, str]]]:
        """
        Auto-create complete Railway setup: project + service + environment.
        
        Returns:
            Tuple of (success, message, setup_info)
        """
        try:
            # Check if we should create
            should_create, reason = self.should_create_project(project_path)
            if not should_create:
                self.logger.info(f"Skipping project creation: {reason}")
                return True, reason, None
            
            # Get project and service names
            final_project_name = self._prompt_for_project_name(project_name)
            if not final_project_name:
                return False, "Project creation cancelled", None
            
            final_service_name = service_name or f"{final_project_name}-service"
            
            # Create project
            project_success, project_message, project_id = self._create_project(final_project_name)
            if not project_success:
                return False, f"Project creation failed: {project_message}", None
            
            # Create service
            service_success, service_message, service_id = self._create_service(
                project_id, final_service_name
            )
            if not service_success:
                return False, f"Service creation failed: {service_message}", None
            
            # Get environment info
            environment_id = self._get_production_environment(project_id)
            
            setup_info = {
                "project_id": project_id,
                "project_name": final_project_name,
                "service_id": service_id,
                "service_name": final_service_name,
                "environment_id": environment_id
            }
            
            return True, f"Created complete Railway setup: {final_project_name}", setup_info
            
        except Exception as e:
            return False, f"Setup creation failed: {str(e)}", None
    
    def _prompt_for_project_name(self, suggested_name: str) -> Optional[str]:
        """Prompt user for project name with suggestion."""
        try:
            clean_name = self._generate_suggested_name(suggested_name)
            print(f"\n🚂 Railway project name: {clean_name}")
            user_input = input("   Use default (press Enter) or enter custom name: ").strip()
            
            if not user_input:
                return clean_name
            
            # Clean custom name
            custom_name = self._generate_suggested_name(user_input)
            return custom_name
            
        except KeyboardInterrupt:
            print("\n❌ Project creation cancelled")
            return None
    
    def _generate_suggested_name(self, project_name: str) -> str:
        """Generate a clean project name."""
        # Clean up project name for Railway
        suggested = project_name.lower().replace(" ", "-").replace("_", "-")
        # Remove invalid characters (Railway allows alphanumeric and hyphens)
        suggested = "".join(c for c in suggested if c.isalnum() or c == "-")
        # Remove leading/trailing hyphens
        suggested = suggested.strip("-")
        return suggested or "my-project"
    
    def _create_project(self, project_name: str) -> Tuple[bool, str, Optional[str]]:
        """Create Railway project using available method."""
        # Try CLI first if available
        if self.use_cli and self.cli_integration.is_cli_available():
            success, message = self.cli_integration.create_project(project_name)
            if success:
                # CLI doesn't return project ID directly, we'll need to get it via API
                if self.api_integration:
                    # List projects to find the newly created one
                    list_success, projects, _ = self.api_integration.list_projects()
                    if list_success:
                        for project in projects:
                            if project.get('name') == project_name:
                                return True, message, project.get('id')
                return True, message, None
            else:
                # Fallback to API if CLI fails
                pass
        
        # Use API
        if self.api_integration:
            return self.api_integration.create_project(project_name)
        else:
            return False, "No authentication method available", None
    
    def _create_service(self, project_id: str, service_name: str) -> Tuple[bool, str, Optional[str]]:
        """Create service within the project."""
        if self.api_integration:
            return self.api_integration.create_service(project_id, service_name)
        else:
            return False, "API integration not available", None
    
    def _get_production_environment(self, project_id: str) -> Optional[str]:
        """Get the production environment ID for the project."""
        if self.api_integration:
            success, project_info, _ = self.api_integration.get_project_info(project_id)
            if success and project_info:
                environments = project_info.get('environments', {}).get('edges', [])
                for env_edge in environments:
                    env_node = env_edge.get('node', {})
                    if env_node.get('name') == 'production':
                        return env_node.get('id')
        return None
