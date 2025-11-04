"""
Railway GraphQL API integration for complete auto-setup.
"""
import requests
from typing import Dict, Optional, Tuple, List
from core.logging import get_logger

class RailwayAPIIntegration:
    """Railway GraphQL API integration for projects, services, and deployments."""
    
    def __init__(self, token: str):
        self.token = token
        self.api_base = "https://backboard.railway.app/graphql"
        self.logger = get_logger(__name__)
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def validate_token(self) -> Tuple[bool, str, Optional[Dict]]:
        """Validate Railway token and get user info."""
        try:
            query = {
                "query": "query { me { id email } }"
            }
            
            response = requests.post(self.api_base, headers=self.headers, json=query)
            
            if response.status_code == 200:
                data = response.json()
                if 'errors' in data:
                    return False, f"Authentication failed: {data['errors'][0]['message']}", None
                
                user_data = data.get('data', {}).get('me')
                if user_data:
                    return True, f"Authenticated as {user_data.get('email')}", user_data
                else:
                    return False, "Invalid token", None
            else:
                return False, f"API error: {response.status_code}", None
                
        except Exception as e:
            return False, f"Connection error: {str(e)}", None
    
    def create_project(self, project_name: str, description: str = "") -> Tuple[bool, str, Optional[str]]:
        """Create a new Railway project."""
        try:
            query = {
                "query": """
                mutation projectCreate($input: ProjectCreateInput!) {
                    projectCreate(input: $input) {
                        id
                        name
                        description
                    }
                }
                """,
                "variables": {
                    "input": {
                        "name": project_name,
                        "description": description or f"Created by DeployX - {project_name}"
                    }
                }
            }
            
            response = requests.post(self.api_base, headers=self.headers, json=query)
            
            if response.status_code == 200:
                data = response.json()
                if 'errors' in data:
                    return False, f"Project creation failed: {data['errors'][0]['message']}", None
                
                project_data = data.get('data', {}).get('projectCreate')
                if project_data:
                    project_id = project_data.get('id')
                    return True, f"Created project: {project_name}", project_id
                else:
                    return False, "Project creation failed", None
            else:
                return False, f"API error: {response.status_code}", None
                
        except Exception as e:
            return False, f"Project creation error: {str(e)}", None
    
    def create_service(self, project_id: str, service_name: str, source_repo: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """Create a service within a project."""
        try:
            service_input = {
                "projectId": project_id,
                "name": service_name
            }
            
            if source_repo:
                service_input["source"] = {
                    "repo": source_repo
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
                    "input": service_input
                }
            }
            
            response = requests.post(self.api_base, headers=self.headers, json=query)
            
            if response.status_code == 200:
                data = response.json()
                if 'errors' in data:
                    return False, f"Service creation failed: {data['errors'][0]['message']}", None
                
                service_data = data.get('data', {}).get('serviceCreate')
                if service_data:
                    service_id = service_data.get('id')
                    return True, f"Created service: {service_name}", service_id
                else:
                    return False, "Service creation failed", None
            else:
                return False, f"API error: {response.status_code}", None
                
        except Exception as e:
            return False, f"Service creation error: {str(e)}", None
    
    def create_deployment(self, service_id: str, environment_id: str) -> Tuple[bool, str, Optional[str]]:
        """Create a deployment for a service."""
        try:
            query = {
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
                        "serviceId": service_id,
                        "environmentId": environment_id
                    }
                }
            }
            
            response = requests.post(self.api_base, headers=self.headers, json=query)
            
            if response.status_code == 200:
                data = response.json()
                if 'errors' in data:
                    return False, f"Deployment failed: {data['errors'][0]['message']}", None
                
                deployment_data = data.get('data', {}).get('deploymentCreate')
                if deployment_data:
                    deployment_id = deployment_data.get('id')
                    deployment_url = deployment_data.get('url')
                    return True, "Deployment created successfully", deployment_id
                else:
                    return False, "Deployment creation failed", None
            else:
                return False, f"API error: {response.status_code}", None
                
        except Exception as e:
            return False, f"Deployment error: {str(e)}", None
    
    def get_project_info(self, project_id: str) -> Tuple[bool, Optional[Dict], str]:
        """Get project information including services and environments."""
        try:
            query = {
                "query": """
                query project($id: String!) {
                    project(id: $id) {
                        id
                        name
                        description
                        services {
                            edges {
                                node {
                                    id
                                    name
                                }
                            }
                        }
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
                "variables": {"id": project_id}
            }
            
            response = requests.post(self.api_base, headers=self.headers, json=query)
            
            if response.status_code == 200:
                data = response.json()
                if 'errors' in data:
                    return False, None, f"Query failed: {data['errors'][0]['message']}"
                
                project_data = data.get('data', {}).get('project')
                if project_data:
                    return True, project_data, "Project info retrieved"
                else:
                    return False, None, "Project not found"
            else:
                return False, None, f"API error: {response.status_code}"
                
        except Exception as e:
            return False, None, f"Query error: {str(e)}"
    
    def list_projects(self) -> Tuple[bool, List[Dict], str]:
        """List all user projects."""
        try:
            query = {
                "query": """
                query {
                    projects {
                        edges {
                            node {
                                id
                                name
                                description
                            }
                        }
                    }
                }
                """
            }
            
            response = requests.post(self.api_base, headers=self.headers, json=query)
            
            if response.status_code == 200:
                data = response.json()
                if 'errors' in data:
                    return False, [], f"Query failed: {data['errors'][0]['message']}"
                
                projects_data = data.get('data', {}).get('projects', {}).get('edges', [])
                projects = [edge['node'] for edge in projects_data]
                return True, projects, f"Found {len(projects)} projects"
            else:
                return False, [], f"API error: {response.status_code}"
                
        except Exception as e:
            return False, [], f"Query error: {str(e)}"
