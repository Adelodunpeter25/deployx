"""
Pydantic models for configuration validation in DeployX.

This module defines the data models used for validating and parsing
configuration files. It uses Pydantic for automatic validation,
type checking, and serialization of configuration data.

The models provide:
    - Strong typing for all configuration fields
    - Automatic validation with clear error messages
    - JSON/YAML serialization support
    - Default values and field descriptions
"""
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator

class ProjectConfig(BaseModel):
    """
    Project configuration model.
    
    Defines the basic project information including name and type.
    This information is used for deployment identification and
    framework-specific build configuration.
    
    Attributes:
        name: Human-readable project name
        type: Project type (react, vue, static, etc.)
    """
    name: str = Field(..., description="Project name")
    type: str = Field(..., description="Project type")

class BuildConfig(BaseModel):
    """
    Build configuration model.
    
    Defines how the project should be built before deployment.
    Includes the build command and output directory specification.
    
    Attributes:
        command: Shell command to build the project (optional)
        output: Directory containing built files for deployment
    """
    command: Optional[str] = Field(None, description="Build command")
    output: str = Field(".", description="Output directory")

class GitHubConfig(BaseModel):
    """
    GitHub Pages platform configuration.
    
    Defines GitHub-specific deployment settings including repository
    information and deployment method (branch or docs folder).
    
    Attributes:
        repo: Repository name in format "owner/repo"
        branch: Target branch for deployment (default: gh-pages)
        method: Deployment method - "branch" or "docs"
    """
    repo: str = Field(..., description="Repository name (owner/repo)")
    branch: str = Field("gh-pages", description="Target branch")
    method: Literal["branch", "docs"] = Field("branch", description="Deployment method")

class VercelConfig(BaseModel):
    """
    Vercel platform configuration.
    
    Defines Vercel-specific deployment settings including project
    and organization identifiers for API access.
    
    Attributes:
        project_id: Vercel project identifier (optional)
        org_id: Vercel organization identifier (optional)
    """
    project_id: Optional[str] = Field(None, description="Vercel project ID")
    org_id: Optional[str] = Field(None, description="Vercel organization ID")

class NetlifyConfig(BaseModel):
    """
    Netlify platform configuration.
    
    Defines Netlify-specific deployment settings including the
    site identifier required for API operations.
    
    Attributes:
        site_id: Netlify site identifier
    """
    site_id: str = Field(..., description="Netlify site ID")

class RailwayConfig(BaseModel):
    """
    Railway platform configuration.
    
    Defines Railway-specific deployment settings including project
    and service identifiers for deployment targeting.
    
    Attributes:
        project_id: Railway project identifier (optional)
        service_id: Railway service identifier (optional)
    """
    project_id: Optional[str] = Field(None, description="Railway project ID")
    service_id: Optional[str] = Field(None, description="Railway service ID")

class RenderConfig(BaseModel):
    """
    Render platform configuration.
    
    Defines Render-specific deployment settings including the
    service identifier required for deployment operations.
    
    Attributes:
        service_id: Render service identifier
    """
    service_id: str = Field(..., description="Render service ID")

class DeployXConfig(BaseModel):
    """
    Main DeployX configuration model.
    
    Root configuration model that combines project, build, and platform
    configurations. Validates that the specified platform has corresponding
    configuration section.
    
    Attributes:
        project: Project information and metadata
        build: Build configuration and commands
        platform: Target deployment platform name
        github: GitHub Pages configuration (optional)
        vercel: Vercel configuration (optional)
        netlify: Netlify configuration (optional)
        railway: Railway configuration (optional)
        render: Render configuration (optional)
    """
    project: ProjectConfig
    build: BuildConfig
    platform: Literal["github", "vercel", "netlify", "railway", "render"]
    
    # Platform-specific configs (only one should be present)
    github: Optional[GitHubConfig] = None
    vercel: Optional[VercelConfig] = None
    netlify: Optional[NetlifyConfig] = None
    railway: Optional[RailwayConfig] = None
    render: Optional[RenderConfig] = None
    
    @validator('platform')
    def validate_platform_config(cls, v, values):
        """
        Ensure platform-specific configuration exists.
        
        Validates that when a platform is specified, the corresponding
        platform configuration section is also provided.
        
        Args:
            v: Platform name value
            values: All field values from the model
            
        Returns:
            Validated platform name
            
        Raises:
            ValueError: If platform config section is missing
        """
        if v not in values or values.get(v) is None:
            raise ValueError(f"Configuration for platform '{v}' is required")
        return v
    
    def get_platform_config(self) -> Dict[str, Any]:
        """
        Get platform-specific configuration as dictionary.
        
        Extracts the configuration section for the specified platform
        and returns it as a dictionary for use with platform classes.
        
        Returns:
            Dictionary containing platform-specific configuration
        """
        platform_config = getattr(self, self.platform)
        return platform_config.dict() if platform_config else {}
