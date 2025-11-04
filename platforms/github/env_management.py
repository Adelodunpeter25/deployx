"""
GitHub environment variables and secrets management.
"""
from typing import Dict, Tuple
from github import Github, GithubException
import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

from core.logging import get_logger
from utils.errors import handle_github_api_error

class GitHubEnvManagement:
    """Handles GitHub repository secrets and environment variables."""
    
    def __init__(self, github_client: Github, repo_name: str):
        self.github_client = github_client
        self.repo_name = repo_name
        self.logger = get_logger(__name__)
        self._repo_obj = None
    
    @property
    def repo_obj(self):
        """Get repository object, cached."""
        if not self._repo_obj:
            self._repo_obj = self.github_client.get_repo(self.repo_name)
        return self._repo_obj
    
    def set_environment_variables(self, env_vars: Dict[str, str]) -> Tuple[bool, str]:
        """Set environment variables as GitHub repository secrets."""
        try:
            if not env_vars:
                return True, "No environment variables to set"
            
            # Get repository public key for encryption
            public_key = self.repo_obj.get_public_key()
            
            success_count = 0
            for key, value in env_vars.items():
                try:
                    # Encrypt the secret value
                    encrypted_value = self._encrypt_secret(value, public_key.key)
                    
                    # Create or update the secret
                    self.repo_obj.create_secret(key, encrypted_value)
                    success_count += 1
                    self.logger.info(f"Set secret: {key}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to set secret {key}: {str(e)}")
            
            if success_count == len(env_vars):
                return True, f"Successfully set {success_count} secrets"
            else:
                return False, f"Set {success_count}/{len(env_vars)} secrets"
                
        except GithubException as e:
            error = handle_github_api_error(e)
            return False, error.message
        except Exception as e:
            return False, f"Failed to set environment variables: {str(e)}"
    
    def get_environment_variables(self) -> Tuple[bool, Dict[str, str], str]:
        """Get environment variables (secret names only, values are not retrievable)."""
        try:
            secrets = self.repo_obj.get_secrets()
            secret_names = {secret.name: "[HIDDEN]" for secret in secrets}
            
            return True, secret_names, f"Found {len(secret_names)} secrets"
            
        except GithubException as e:
            error = handle_github_api_error(e)
            return False, {}, error.message
        except Exception as e:
            return False, {}, f"Failed to get environment variables: {str(e)}"
    
    def delete_environment_variable(self, key: str) -> Tuple[bool, str]:
        """Delete an environment variable (secret)."""
        try:
            secret = self.repo_obj.get_secret(key)
            secret.delete()
            
            return True, f"Successfully deleted secret: {key}"
            
        except GithubException as e:
            if e.status == 404:
                return False, f"Secret not found: {key}"
            error = handle_github_api_error(e)
            return False, error.message
        except Exception as e:
            return False, f"Failed to delete secret {key}: {str(e)}"
    
    def _encrypt_secret(self, secret_value: str, public_key: str) -> str:
        """Encrypt a secret value using the repository's public key."""
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives import hashes
        import base64
        
        # Load the public key
        public_key_obj = serialization.load_pem_public_key(public_key.encode())
        
        # Encrypt the secret
        encrypted = public_key_obj.encrypt(
            secret_value.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Return base64 encoded encrypted value
        return base64.b64encode(encrypted).decode()
