"""
Service type detection for Render platform.

Analyzes project structure to determine the appropriate Render service type
and configuration based on project characteristics.
"""
from pathlib import Path
from typing import Tuple, Optional
import json

class RenderServiceDetector:
    """Detects appropriate Render service type for projects."""
    
    @staticmethod
    def detect_service_type(project_path: str, project_type: str) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Detect Render service type based on project characteristics.
        
        Args:
            project_path: Path to project directory
            project_type: Detected project type (react, vue, django, flask, etc.)
            
        Returns:
            Tuple of (service_type, build_command, publish_path)
        """
        path = Path(project_path)
        
        # Static site projects
        if project_type in ["react", "vue", "angular", "static", "nextjs"]:
            return RenderServiceDetector._detect_static_site(path, project_type)
        
        # Web service projects (including Python frameworks)
        elif project_type in ["nodejs", "express", "python", "django", "flask", "fastapi"]:
            return RenderServiceDetector._detect_web_service(path, project_type)
        
        # Default to static site for unknown types
        else:
            return "static_site", None, "."
    
    @staticmethod
    def _detect_static_site(path: Path, project_type: str) -> Tuple[str, Optional[str], str]:
        """Detect static site configuration."""
        build_command = None
        publish_path = "."
        
        # Check for package.json to determine build command
        package_json_path = path / "package.json"
        if package_json_path.exists():
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                
                scripts = package_data.get("scripts", {})
                if "build" in scripts:
                    # Detect package manager
                    if (path / "yarn.lock").exists():
                        build_command = "yarn install && yarn build"
                    elif (path / "pnpm-lock.yaml").exists():
                        build_command = "pnpm install && pnpm build"
                    elif (path / "bun.lockb").exists():
                        build_command = "bun install && bun run build"
                    else:
                        build_command = "npm install && npm run build"
                
                # Determine publish path based on project type
                if project_type == "react":
                    publish_path = "build"
                elif project_type in ["vue", "angular"]:
                    publish_path = "dist"
                elif project_type == "nextjs":
                    publish_path = "out"
                    
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return "static_site", build_command, publish_path
    
    @staticmethod
    def _detect_web_service(path: Path, project_type: str) -> Tuple[str, Optional[str], Optional[str]]:
        """Detect web service configuration."""
        build_command = None
        
        if project_type in ["nodejs", "express"]:
            # Check for package.json
            package_json_path = path / "package.json"
            if package_json_path.exists():
                try:
                    with open(package_json_path, 'r') as f:
                        package_data = json.load(f)
                    
                    scripts = package_data.get("scripts", {})
                    if "build" in scripts:
                        if (path / "yarn.lock").exists():
                            build_command = "yarn install && yarn build"
                        else:
                            build_command = "npm install && npm run build"
                    else:
                        # Just install dependencies
                        if (path / "yarn.lock").exists():
                            build_command = "yarn install"
                        else:
                            build_command = "npm install"
                            
                except (json.JSONDecodeError, FileNotFoundError):
                    build_command = "npm install"
        
        elif project_type in ["python", "django", "flask", "fastapi"]:
            # Python projects - detect package manager and dependencies
            if (path / "requirements.txt").exists():
                build_command = "pip install -r requirements.txt"
            elif (path / "pyproject.toml").exists():
                # Check if using poetry, pipenv, or standard pip
                try:
                    with open(path / "pyproject.toml", 'r') as f:
                        content = f.read()
                    if "[tool.poetry" in content:
                        build_command = "poetry install --only=main"
                    else:
                        build_command = "pip install ."
                except FileNotFoundError:
                    build_command = "pip install ."
            elif (path / "Pipfile").exists():
                build_command = "pipenv install --deploy"
            elif (path / "setup.py").exists():
                build_command = "pip install ."
            else:
                # Fallback for Python projects
                build_command = "pip install -r requirements.txt"
            
            # Add Django-specific build steps
            if project_type == "django":
                if build_command:
                    build_command += " && python manage.py collectstatic --noinput"
                else:
                    build_command = "python manage.py collectstatic --noinput"
        
        return "web_service", build_command, None
    
    @staticmethod
    def generate_service_name(project_name: str, existing_services: list) -> str:
        """
        Generate unique service name.
        
        Args:
            project_name: Base project name
            existing_services: List of existing service names
            
        Returns:
            Unique service name
        """
        # Clean project name
        base_name = project_name.lower().replace("_", "-").replace(" ", "-")
        base_name = "".join(c for c in base_name if c.isalnum() or c == "-")
        
        # Check if base name is available
        existing_names = [service.name for service in existing_services]
        
        if base_name not in existing_names:
            return base_name
        
        # Add suffix if name exists
        counter = 1
        while f"{base_name}-{counter}" in existing_names:
            counter += 1
        
        return f"{base_name}-{counter}"
