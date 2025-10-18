"""
Comprehensive error handling for DeployX
"""

import time
import requests
from typing import Callable, Any
from functools import wraps

from .ui import warning, info

class DeployXError(Exception):
    """Base exception for DeployX errors"""
    def __init__(self, message: str, suggestions: list = None):
        self.message = message
        self.suggestions = suggestions or []
        super().__init__(message)

class NetworkError(DeployXError):
    """Network connectivity issues"""
    pass

class AuthenticationError(DeployXError):
    """Authentication and authorization issues"""
    pass

class BuildError(DeployXError):
    """Build process failures"""
    pass

class GitError(DeployXError):
    """Git repository issues"""
    pass

class GitHubAPIError(DeployXError):
    """GitHub API specific errors"""
    pass

def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retrying operations with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (requests.ConnectionError, requests.Timeout, NetworkError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        warning(f"Network error, retrying in {delay:.1f}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                    else:
                        raise NetworkError(
                            "Network connection failed after multiple attempts",
                            [
                                "Check your internet connection",
                                "Verify the service is accessible",
                                "Try again in a few minutes",
                                "Check if you're behind a firewall or proxy"
                            ]
                        ) from e
                except Exception as e:
                    # Don't retry non-network errors
                    raise e
            
            raise last_exception
        return wrapper
    return decorator

def handle_network_error(e: Exception) -> NetworkError:
    """Convert network exceptions to NetworkError with suggestions"""
    if "timeout" in str(e).lower():
        return NetworkError(
            "Request timed out",
            [
                "Check your internet connection speed",
                "Try again with a more stable connection",
                "The service might be experiencing high load"
            ]
        )
    elif "connection" in str(e).lower():
        return NetworkError(
            "Could not connect to service",
            [
                "Check your internet connection",
                "Verify the service URL is correct",
                "Check if you're behind a firewall",
                "Try using a VPN if in a restricted network"
            ]
        )
    else:
        return NetworkError(
            f"Network error: {str(e)}",
            [
                "Check your internet connection",
                "Try again in a few minutes"
            ]
        )

def handle_auth_error(platform: str, error_msg: str) -> AuthenticationError:
    """Handle authentication errors with platform-specific guidance"""
    suggestions = []
    
    if platform == "github":
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            suggestions = [
                "Check your GitHub personal access token",
                "Generate a new token at: https://github.com/settings/tokens",
                "Ensure token has 'repo' and 'workflow' permissions",
                "Set the token in GITHUB_TOKEN environment variable",
                "Verify the token hasn't expired"
            ]
        elif "403" in error_msg or "forbidden" in error_msg.lower():
            suggestions = [
                "Check repository permissions - you need write access",
                "Verify the repository exists and is accessible",
                "Check if the repository is private and token has access",
                "Ensure token has sufficient permissions (repo scope)"
            ]
        elif "rate limit" in error_msg.lower():
            suggestions = [
                "GitHub API rate limit exceeded",
                "Wait for the rate limit to reset (usually 1 hour)",
                "Use a personal access token for higher limits",
                "Check rate limit status at: https://api.github.com/rate_limit"
            ]
    
    return AuthenticationError(f"Authentication failed: {error_msg}", suggestions)

def handle_build_error(command: str, output: str, error_output: str) -> BuildError:
    """Handle build errors with helpful suggestions"""
    suggestions = [
        f"Build command failed: {command}",
        "Check the build output above for specific errors"
    ]
    
    # Analyze common build issues
    combined_output = (output + error_output).lower()
    
    if "npm" in command and "not found" in combined_output:
        suggestions.extend([
            "Install dependencies: npm install",
            "Check if Node.js and npm are installed",
            "Verify package.json exists and is valid"
        ])
    elif "permission denied" in combined_output:
        suggestions.extend([
            "Check file permissions in your project",
            "Try running with appropriate permissions",
            "Ensure output directory is writable"
        ])
    elif "out of memory" in combined_output or "heap" in combined_output:
        suggestions.extend([
            "Build ran out of memory",
            "Try: NODE_OPTIONS='--max-old-space-size=4096' npm run build",
            "Close other applications to free memory",
            "Consider optimizing your build process"
        ])
    elif "module not found" in combined_output or "cannot resolve" in combined_output:
        suggestions.extend([
            "Missing dependencies detected",
            "Run: npm install or yarn install",
            "Check import paths in your code",
            "Verify all required packages are in package.json"
        ])
    
    # Show relevant error lines (last 10 lines of error output)
    if error_output:
        error_lines = error_output.strip().split('\n')[-10:]
        suggestions.append("Recent error output:")
        suggestions.extend([f"  {line}" for line in error_lines])
    
    return BuildError("Build process failed", suggestions)

def handle_git_error(e: Exception) -> GitError:
    """Handle git-related errors"""
    error_msg = str(e).lower()
    
    if "not a git repository" in error_msg:
        return GitError(
            "Not a git repository",
            [
                "Initialize git repository: git init",
                "Add files: git add .",
                "Make initial commit: git commit -m 'Initial commit'",
                "Add remote: git remote add origin <repository-url>"
            ]
        )
    elif "uncommitted changes" in error_msg or "working tree clean" in error_msg:
        return GitError(
            "Uncommitted changes detected",
            [
                "Commit your changes: git add . && git commit -m 'Your message'",
                "Or stash changes: git stash",
                "Check status: git status"
            ]
        )
    elif "merge conflict" in error_msg or "conflict" in error_msg:
        return GitError(
            "Git merge conflict detected",
            [
                "Resolve conflicts in your files",
                "Add resolved files: git add <file>",
                "Complete merge: git commit",
                "Or abort merge: git merge --abort"
            ]
        )
    elif "remote" in error_msg and "not found" in error_msg:
        return GitError(
            "Git remote not configured",
            [
                "Add remote repository: git remote add origin <url>",
                "Check remotes: git remote -v",
                "Verify repository URL is correct"
            ]
        )
    else:
        return GitError(
            f"Git operation failed: {str(e)}",
            [
                "Check git status: git status",
                "Verify repository is in good state",
                "Try git pull to sync with remote"
            ]
        )

def handle_github_api_error(e: Exception) -> GitHubAPIError:
    """Handle GitHub API specific errors"""
    error_msg = str(e)
    
    if "404" in error_msg:
        return GitHubAPIError(
            "Repository not found",
            [
                "Verify repository name format: owner/repository",
                "Check if repository exists on GitHub",
                "Ensure you have access to the repository",
                "Check if repository is private and token has access"
            ]
        )
    elif "rate limit" in error_msg.lower():
        return GitHubAPIError(
            "GitHub API rate limit exceeded",
            [
                "Wait for rate limit reset (check headers for reset time)",
                "Use authenticated requests for higher limits",
                "Check current limits: https://api.github.com/rate_limit",
                "Consider using GitHub Apps for higher limits"
            ]
        )
    elif "abuse" in error_msg.lower():
        return GitHubAPIError(
            "GitHub abuse detection triggered",
            [
                "Slow down API requests",
                "Wait a few minutes before retrying",
                "Avoid rapid successive API calls",
                "Contact GitHub support if issue persists"
            ]
        )
    else:
        return GitHubAPIError(
            f"GitHub API error: {error_msg}",
            [
                "Check GitHub status: https://www.githubstatus.com/",
                "Verify your token permissions",
                "Try again in a few minutes"
            ]
        )

def display_error_with_suggestions(error: DeployXError) -> None:
    """Display error message with actionable suggestions"""
    error(f"❌ {error.message}")
    
    if error.suggestions:
        info("💡 Suggested solutions:")
        for i, suggestion in enumerate(error.suggestions, 1):
            if suggestion.startswith("  "):  # Indented output
                print(suggestion)
            else:
                print(f"   {i}. {suggestion}")

def safe_execute(func: Callable, *args, **kwargs) -> Any:
    """Safely execute a function with comprehensive error handling"""
    try:
        return func(*args, **kwargs)
    except DeployXError:
        # Re-raise our custom errors
        raise
    except requests.exceptions.ConnectionError as e:
        raise handle_network_error(e)
    except requests.exceptions.Timeout as e:
        raise handle_network_error(e)
    except Exception as e:
        # Convert unknown exceptions to generic DeployXError
        raise DeployXError(
            f"Unexpected error: {str(e)}",
            [
                "This might be a bug in DeployX",
                "Try running with --verbose for more details",
                "Report this issue at: https://github.com/deployx/deployx/issues"
            ]
        )