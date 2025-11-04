"""
Netlify site auto-creation functionality.
"""
from typing import Tuple, Optional
from pathlib import Path
from core.logging import get_logger
from .api_integration import NetlifyAPIIntegration
from .cli_integration import NetlifyCLIIntegration

class NetlifyAutoCreation:
    """Handles automatic Netlify site creation and setup."""
    
    def __init__(self, token: str, use_cli: bool = True):
        self.token = token
        self.use_cli = use_cli
        self.logger = get_logger(__name__)
        
        if use_cli:
            self.cli_integration = NetlifyCLIIntegration()
        
        if token:
            self.api_integration = NetlifyAPIIntegration(token)
        else:
            self.api_integration = None
    
    def should_create_site(self, project_path: str = ".") -> Tuple[bool, str]:
        """
        Determine if we should auto-create a Netlify site.
        
        Returns:
            Tuple of (should_create, reason)
        """
        # Check for existing Netlify configuration
        netlify_config = Path(project_path) / '.netlify'
        if netlify_config.exists():
            return False, "Netlify site already configured"
        
        # Check for netlify.toml
        netlify_toml = Path(project_path) / 'netlify.toml'
        if netlify_toml.exists():
            return False, "netlify.toml found, site may already exist"
        
        return True, "No Netlify site detected"
    
    def auto_create_site(self, site_name: str, project_path: str = ".", custom_domain: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Auto-create Netlify site and configure it.
        
        Returns:
            Tuple of (success, message, site_id)
        """
        try:
            # Check if we should create
            should_create, reason = self.should_create_site(project_path)
            if not should_create:
                self.logger.info(f"Skipping site creation: {reason}")
                return True, reason, None
            
            # Get suggested site name
            suggested_name = self._generate_suggested_name(site_name)
            
            # Prompt user for site name
            final_name = self._prompt_for_site_name(suggested_name)
            if not final_name:
                return False, "Site creation cancelled", None
            
            # Try CLI first if available
            if self.use_cli and self.cli_integration.is_cli_available():
                return self._create_via_cli(final_name, project_path)
            
            # Fallback to API
            elif self.api_integration:
                return self._create_via_api(final_name, custom_domain)
            
            else:
                return False, "No authentication method available", None
                
        except Exception as e:
            return False, f"Failed to create site: {str(e)}", None
    
    def _generate_suggested_name(self, site_name: str) -> str:
        """Generate a suggested site name."""
        # Clean up site name for Netlify
        suggested = site_name.lower().replace(" ", "-").replace("_", "-")
        # Remove invalid characters (Netlify allows alphanumeric and hyphens)
        suggested = "".join(c for c in suggested if c.isalnum() or c == "-")
        # Remove leading/trailing hyphens
        suggested = suggested.strip("-")
        return suggested or "my-site"
    
    def _prompt_for_site_name(self, suggested_name: str) -> Optional[str]:
        """Prompt user for site name with suggestion."""
        try:
            print(f"\n🌐 Netlify site name: {suggested_name}")
            user_input = input("   Use default (press Enter) or enter custom name: ").strip()
            
            if not user_input:
                return suggested_name
            
            # Clean custom name
            custom_name = self._generate_suggested_name(user_input)
            return custom_name
            
        except KeyboardInterrupt:
            print("\n❌ Site creation cancelled")
            return None
    
    def _create_via_cli(self, site_name: str, project_path: str) -> Tuple[bool, str, Optional[str]]:
        """Create site using Netlify CLI."""
        success, message, site_id = self.cli_integration.create_site(site_name, project_path)
        
        if success:
            # Link the site to current directory
            if site_id:
                link_success, link_message = self.cli_integration.link_site(site_id, project_path)
                if not link_success:
                    self.logger.warning(f"Site created but linking failed: {link_message}")
            
            return True, message, site_id
        else:
            return False, message, None
    
    def _create_via_api(self, site_name: str, custom_domain: Optional[str]) -> Tuple[bool, str, Optional[str]]:
        """Create site using Netlify API."""
        success, message, site_id = self.api_integration.create_site(site_name, custom_domain)
        
        if success:
            # Create .netlify directory with site info
            try:
                netlify_dir = Path('.netlify')
                netlify_dir.mkdir(exist_ok=True)
                
                state_file = netlify_dir / 'state.json'
                with open(state_file, 'w') as f:
                    import json
                    json.dump({"siteId": site_id}, f)
                
                self.logger.info(f"Created .netlify/state.json with site ID: {site_id}")
            except Exception as e:
                self.logger.warning(f"Could not create .netlify/state.json: {e}")
            
            return True, message, site_id
        else:
            return False, message, None
