"""
Railway deployment platform implementation
"""

import os
import requests
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from .base import BasePlatform, DeploymentResult, DeploymentStatus
from utils.errors import AuthenticationError

class RailwayPlatform(BasePlatform):
    """Railway deployment platform"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_base = "https://backboard.railway.app/graphql"
        self.project_path = config.get('project_path', '.')
        self.token = self._get_token()
        self.project_id = config.get("railway", {}).get("project_id")
        
    def _get_token(self) -> str:
        """Get Railway token from file or environment"""
        token_file = Path('.deployx_railway_token')
        
        if token_file.exists():
            try:
                with open(token_file, 'r') as f:
                    return f.read().strip()
            except Exception:
                pass
            
        token = os.getenv("RAILWAY_TOKEN")
        if not token:
            raise AuthenticationError("Railway token not found. Run 'deployx init' to configure.")
        return token
    
    def validate_credentials(self) -> Tuple[bool, str]:
        """Validate Railway credentials"""
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            query = {
                "query": "query { me { id email } }"
            }
            
            response = requests.post(self.api_base, headers=headers, json=query)
            
            if response.status_code == 200:
                data = response.json()
                if "errors" not in data:
                    user = data.get("data", {}).get("me", {})
                    return True, f"Authenticated as {user.get('email', 'user')}"
                else:
                    return False, "Invalid token"
            else:
                return False, f"Authentication failed (HTTP {response.status_code})"
                
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def prepare_deployment(self, project_path: str, build_command: Optional[str], output_dir: str) -> Tuple[bool, str]:
        """Prepare deployment files"""
        try:
            # Check for Railway configuration files
            railway_files = [
                "railway.toml",
                "railway.json", 
                "Procfile",
                "Dockerfile"
            ]
            
            has_config = any((Path(self.project_path) / f).exists() for f in railway_files)
            
            if not has_config:
                # Create basic railway.toml
                config_content = f"""[build]
builder = "nixpacks"

[deploy]
startCommand = "{self._get_start_command()}"
"""
                railway_config = Path(self.project_path) / "railway.toml"
                railway_config.write_text(config_content)
            
            return True, "Deployment prepared successfully"
            
        except Exception as e:
            return False, f"Preparation failed: {str(e)}"
    
    def _get_start_command(self) -> str:
        """Get appropriate start command based on project type"""
        project_type = self.config.get("project", {}).get("type", "")
        
        start_commands = {
            "django": "python manage.py runserver 0.0.0.0:$PORT",
            "flask": "python app.py",
            "fastapi": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            "node": "npm start",
            "react": "npm start",
            "nextjs": "npm start"
        }
        
        return start_commands.get(project_type, "npm start")
    
    def execute_deployment(self, project_path: str, output_dir: str) -> DeploymentResult:
        """Execute deployment to Railway"""
        try:
            # Use Railway CLI if available, otherwise use API
            if self._has_railway_cli():
                success, message, url = self._deploy_with_cli()
            else:
                success, message, url = self._deploy_with_api()
            
            return DeploymentResult(success=success, url=url, message=message)
                
        except Exception as e:
            return DeploymentResult(success=False, message=f"Deployment failed: {str(e)}")
    
    def _has_railway_cli(self) -> bool:
        """Check if Railway CLI is available"""
        try:
            subprocess.run(["railway", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _deploy_with_cli(self) -> Tuple[bool, str, Optional[str]]:
        """Deploy using Railway CLI"""
        try:
            # Set token for CLI
            env = os.environ.copy()
            env["RAILWAY_TOKEN"] = self.token
            
            # Login and deploy
            subprocess.run(["railway", "login"], env=env, check=True)
            
            # Link to project if project_id exists
            if self.project_id:
                subprocess.run(["railway", "link", self.project_id], env=env, check=True)
            
            # Deploy
            result = subprocess.run(
                ["railway", "up"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode == 0:
                # Get deployment URL
                url_result = subprocess.run(
                    ["railway", "domain"],
                    cwd=self.project_path,
                    capture_output=True,
                    text=True,
                    env=env
                )
                
                url = None
                if url_result.returncode == 0:
                    lines = url_result.stdout.strip().split('\n')
                    for line in lines:
                        if line.startswith('https://'):
                            url = line.strip()
                            break
                
                return True, "Deployment successful", url
            else:
                return False, f"CLI deployment failed: {result.stderr}", None
                
        except Exception as e:
            return False, f"CLI deployment error: {str(e)}", None
    
    def _deploy_with_api(self) -> Tuple[bool, str, Optional[str]]:
        """Deploy using Railway API (simplified)"""
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            # Create project if needed
            if not self.project_id:
                query = {
                    "query": """
                    mutation projectCreate($input: ProjectCreateInput!) {
                        projectCreate(input: $input) {
                            id
                            name
                        }
                    }
                    """,
                    "variables": {
                        "input": {
                            "name": self.config.get("project", {}).get("name", "deployx-app")
                        }
                    }
                }
                
                response = requests.post(self.api_base, headers=headers, json=query)
                if response.status_code == 200:
                    data = response.json()
                    if "errors" not in data:
                        self.project_id = data["data"]["projectCreate"]["id"]
                    else:
                        return False, "Failed to create project", None
                else:
                    return False, f"Project creation failed (HTTP {response.status_code})", None
            
            # Create deployment via API
            deployment_query = {
                "query": """
                    mutation deploymentCreate($input: DeploymentCreateInput!) {
                        deploymentCreate(input: $input) {
                            id
                            status
                            url
                        }
                    }
                """,
                "variables": {
                    "input": {
                        "projectId": self.project_id,
                        "environmentId": self._get_environment_id(),
                        "serviceId": self.service_id or self._create_service()
                    }
                }
            }
            
            response = requests.post(self.api_base, headers=headers, json=deployment_query)
            if response.status_code == 200:
                data = response.json()
                if "errors" not in data:
                    deployment = data["data"]["deploymentCreate"]
                    deployment_url = deployment.get("url")
                    if deployment_url and not deployment_url.startswith("http"):
                        deployment_url = f"https://{deployment_url}"
                    
                    return True, "Deployment created successfully", deployment_url
                else:
                    errors = data.get("errors", [])
                    error_msg = errors[0].get("message", "Unknown error") if errors else "Deployment failed"
                    return False, f"Deployment failed: {error_msg}", None
            else:
                return False, f"Deployment failed (HTTP {response.status_code})", None
                
        except Exception as e:
            return False, f"API deployment error: {str(e)}", None
    
    def _get_environment_id(self) -> str:
        """Get the production environment ID for the project."""
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            query = {
                "query": """
                    query project($id: String!) {
                        project(id: $id) {
                            environments {
                                edges {
                                    node {
                                        id
                                        name
                                    }
                                }
                            }
                        }
                    }
                """,
                "variables": {"id": self.project_id}
            }
            
            response = requests.post(self.api_base, headers=headers, json=query)
            if response.status_code == 200:
                data = response.json()
                environments = data["data"]["project"]["environments"]["edges"]
                
                # Find production environment or use first available
                for env in environments:
                    if env["node"]["name"].lower() == "production":
                        return env["node"]["id"]
                
                # Return first environment if production not found
                if environments:
                    return environments[0]["node"]["id"]
            
            return "production"  # Fallback
            
        except Exception:
            return "production"  # Fallback
    
    def _create_service(self) -> str:
        """Create a service for the project if none exists."""
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            query = {
                "query": """
                    mutation serviceCreate($input: ServiceCreateInput!) {
                        serviceCreate(input: $input) {
                            id
                            name
                        }
                    }
                """,
                "variables": {
                    "input": {
                        "projectId": self.project_id,
                        "name": self.config.get("project", {}).get("name", "deployx-service"),
                        "source": {
                            "repo": self._get_repo_url() or "https://github.com/user/repo"
                        }
                    }
                }
            }
            
            response = requests.post(self.api_base, headers=headers, json=query)
            if response.status_code == 200:
                data = response.json()
                if "errors" not in data:
                    return data["data"]["serviceCreate"]["id"]
            
            return "default-service"  # Fallback
            
        except Exception:
            return "default-service"  # Fallback
    
    def _get_repo_url(self) -> Optional[str]:
        """Get Git repository URL from project."""
        try:
            import git
            repo = git.Repo(self.project_path)
            origin = repo.remote('origin')
            return origin.url
        except Exception:
            return None
    
    def get_status(self, deployment_id: Optional[str] = None) -> DeploymentStatus:
        """Get deployment status"""
        try:
            if not self.project_id:
                return DeploymentStatus(status="unknown", message="No project ID configured")
                
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            query = {
                "query": """
                query project($id: String!) {
                    project(id: $id) {
                        services {
                            edges {
                                node {
                                    id
                                    name
                                    deployments {
                                        edges {
                                            node {
                                                id
                                                status
                                                url
                                                createdAt
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                """,
                "variables": {"id": self.project_id}
            }
            
            response = requests.post(self.api_base, headers=headers, json=query)
            
            if response.status_code == 200:
                data = response.json()
                if "errors" not in data:
                    services = data.get("data", {}).get("project", {}).get("services", {}).get("edges", [])
                    if services:
                        service = services[0]["node"]
                        deployments = service.get("deployments", {}).get("edges", [])
                        if deployments:
                            deployment = deployments[0]["node"]
                            status = deployment.get("status", "unknown").lower()
                            
                            status_map = {
                                "success": "ready",
                                "building": "building",
                                "failed": "error",
                                "crashed": "error"
                            }
                            
                            return DeploymentStatus(
                                status=status_map.get(status, "unknown"),
                                url=deployment.get("url"),
                                last_updated=deployment.get("createdAt"),
                                message=f"Railway deployment {status}"
                            )
            
            return DeploymentStatus(status="unknown", message="No deployments found")
            
        except Exception as e:
            return DeploymentStatus(status="error", message=f"Status check failed: {str(e)}")
    
    def get_url(self) -> Optional[str]:
        """Get deployment URL"""
        status = self.get_status()
        return status.url