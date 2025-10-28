"""
Project type and framework detection for DeployX.

Automatically detects project type, framework, build tools, and
package managers by analyzing project files and dependencies.

Detection priority:
1. Node.js projects (package.json)
2. Python projects (requirements.txt, pyproject.toml, etc.)
3. Static sites (index.html)

Example:
    >>> info = detect_project("./my-react-app")
    >>> info.type
    'react'
    >>> info.build_command
    'npm run build'
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List


class ProjectInfo:
    """
    Container for detected project information.
    
    Attributes:
        type: Project type (react, vue, django, static, etc.)
        framework: Specific framework name if applicable
        build_command: Command to build the project
        output_dir: Directory where build outputs are placed
        package_manager: Package manager in use (npm, yarn, pip, etc.)
        detected_files: List of files used for detection
    """
    
    def __init__(self):
        self.type: str = "unknown"
        self.framework: Optional[str] = None
        self.build_command: Optional[str] = None
        self.output_dir: str = "."
        self.package_manager: str = "npm"
        self.detected_files: List[str] = []


def detect_project(project_path: str = ".") -> ProjectInfo:
    """
    Detect project type, framework, and build settings.
    
    Analyzes project files to determine the type of project,
    framework being used, and appropriate build configuration.
    
    Args:
        project_path: Path to project directory (default: current directory)
    
    Returns:
        ProjectInfo object with detected information
    
    Example:
        >>> info = detect_project("./my-app")
        >>> print(f"{info.type} project using {info.package_manager}")
    """
    path = Path(project_path)
    info = ProjectInfo()
    
    # Priority 1: Node.js projects (most common for web deployments)
    if (path / "package.json").exists():
        info = _detect_nodejs_project(path)
    # Priority 2: Python projects
    elif any((path / f).exists() for f in ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"]):
        info = _detect_python_project(path)
    # Priority 3: Static HTML sites (root level)
    elif (path / "index.html").exists():
        info.type = "static"
        info.output_dir = "."
        info.detected_files.append("index.html")
    # Priority 4: Static HTML sites (public folder)
    elif (path / "public" / "index.html").exists():
        info.type = "static"
        info.output_dir = "public"
        info.detected_files.append("public/index.html")
    
    return info


def _detect_nodejs_project(path: Path) -> ProjectInfo:
    """
    Detect Node.js project details from package.json.
    
    Analyzes dependencies to identify framework (React, Vue, Next.js, etc.)
    and determines appropriate build command and output directory.
    
    Args:
        path: Path to project directory
    
    Returns:
        ProjectInfo with Node.js project details
    """
    info = ProjectInfo()
    info.type = "nodejs"
    info.detected_files.append("package.json")
    
    try:
        with open(path / "package.json", 'r') as f:
            package_json = json.load(f)
        
        # Combine dependencies and devDependencies for framework detection
        deps = {
            **package_json.get("dependencies", {}),
            **package_json.get("devDependencies", {})
        }
        
        # Check for Vite first (modern build tool, special handling needed)
        if "vite" in deps:
            info = _detect_vite_project(path, deps, package_json)
        # React (Create React App or similar)
        elif "react" in deps:
            info.framework = "react"
            info.type = "react"
            info.output_dir = "build"  # CRA default
        # Next.js (React framework with SSR)
        elif "next" in deps:
            info.framework = "nextjs"
            info.type = "nextjs"
            info.output_dir = "out"  # Next.js static export
        # Vue.js
        elif "vue" in deps:
            info.framework = "vue"
            info.type = "vue"
            info.output_dir = "dist"  # Vue CLI default
        # Angular
        elif "@angular/core" in deps:
            info.framework = "angular"
            info.type = "angular"
            info.output_dir = "dist"
        # Express (backend framework)
        elif "express" in deps:
            info.framework = "express"
            info.type = "nodejs"
            info.output_dir = "."
        
        # Detect build command from package.json scripts
        scripts = package_json.get("scripts", {})
        if "build" in scripts:
            pm = _detect_package_manager(path)
            info.build_command = f"{pm} run build"
        
        # Set package manager
        info.package_manager = _detect_package_manager(path)
        info.detected_files.append("package.json")
        
    except (json.JSONDecodeError, FileNotFoundError):
        # If package.json is malformed or missing, return basic info
        pass
    
    return info


def _detect_vite_project(path: Path, deps: Dict, package_json: Dict) -> ProjectInfo:
    """
    Detect Vite-based projects.
    
    Vite is a modern build tool that can be used with React, Vue, or vanilla JS.
    Requires special detection to identify the underlying framework.
    
    Args:
        path: Path to project directory
        deps: Combined dependencies from package.json
        package_json: Parsed package.json content
    
    Returns:
        ProjectInfo with Vite project details
    """
    info = ProjectInfo()
    info.framework = "vite"
    info.output_dir = "dist"  # Vite default output
    info.detected_files.extend(["package.json"])
    
    # Look for Vite config file (helps confirm Vite usage)
    vite_configs = ["vite.config.js", "vite.config.ts", "vite.config.mjs"]
    for config in vite_configs:
        if (path / config).exists():
            info.detected_files.append(config)
            break
    
    # Determine which framework is being used with Vite
    if "react" in deps:
        info.type = "react"
        info.framework = "react-vite"
    elif "vue" in deps:
        info.type = "vue"
        info.framework = "vue-vite"
    else:
        # Vanilla Vite project
        info.type = "vite"
    
    return info


def _detect_python_project(path: Path) -> ProjectInfo:
    """
    Detect Python project details.
    
    Analyzes requirements files to identify framework (Django, Flask, FastAPI)
    and determines appropriate build command if needed.
    
    Args:
        path: Path to project directory
    
    Returns:
        ProjectInfo with Python project details
    """
    info = ProjectInfo()
    info.type = "python"
    info.package_manager = _detect_python_package_manager(path)
    
    # Read requirements to detect framework
    requirements = _read_python_requirements(path)
    
    # Django (full-featured web framework)
    if "django" in requirements:
        info.framework = "django"
        info.type = "django"
        # Django needs to collect static files before deployment
        info.build_command = "python manage.py collectstatic --noinput"
        info.output_dir = "staticfiles"
    # Flask (micro web framework)
    elif "flask" in requirements:
        info.framework = "flask"
        info.type = "flask"
        info.output_dir = "."
    # FastAPI (modern async web framework)
    elif "fastapi" in requirements:
        info.framework = "fastapi"
        info.type = "fastapi"
        info.output_dir = "."
    
    # Track which files were found for detection
    for file in ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"]:
        if (path / file).exists():
            info.detected_files.append(file)
    
    return info


def _read_python_requirements(path: Path) -> List[str]:
    """
    Read Python requirements from various file formats.
    
    Supports requirements.txt and pyproject.toml formats.
    Extracts package names without version specifiers.
    
    Args:
        path: Path to project directory
    
    Returns:
        List of lowercase package names
    """
    requirements = []
    
    # Parse requirements.txt (most common format)
    if (path / "requirements.txt").exists():
        try:
            with open(path / "requirements.txt", 'r') as f:
                for line in f:
                    # Skip comments and empty lines
                    if line.strip() and not line.startswith('#'):
                        # Extract package name (remove version specifiers)
                        pkg = line.split('==')[0].split('>=')[0].split('<=')[0].strip()
                        requirements.append(pkg)
        except Exception:
            pass
    
    # Parse pyproject.toml (modern Python packaging)
    if (path / "pyproject.toml").exists():
        try:
            import tomllib
            with open(path / "pyproject.toml", 'rb') as f:
                data = tomllib.load(f)
                deps = data.get('project', {}).get('dependencies', [])
                for dep in deps:
                    # Extract package name
                    pkg = dep.split('==')[0].split('>=')[0].split('<=')[0].strip()
                    requirements.append(pkg)
        except Exception:
            pass
    
    # Return lowercase for case-insensitive matching
    return [req.lower() for req in requirements]


def _detect_python_package_manager(path: Path) -> str:
    """
    Detect Python package manager from lock files.
    
    Checks for lock files in priority order:
    1. uv (fastest, modern)
    2. pipenv (Pipfile)
    3. poetry (poetry.lock)
    4. pip (default)
    
    Args:
        path: Path to project directory
    
    Returns:
        Package manager name
    """
    if (path / "uv.lock").exists():
        return "uv"
    elif (path / "Pipfile").exists():
        return "pipenv"
    elif (path / "poetry.lock").exists():
        return "poetry"
    elif (path / "pyproject.toml").exists():
        return "pip"
    else:
        return "pip"


def _detect_package_manager(path: Path) -> str:
    """
    Detect Node.js package manager from lock files.
    
    Checks for lock files in priority order:
    1. yarn (yarn.lock)
    2. pnpm (pnpm-lock.yaml)
    3. bun (bun.lockb)
    4. npm (default)
    
    Args:
        path: Path to project directory
    
    Returns:
        Package manager name
    """
    if (path / "yarn.lock").exists():
        return "yarn"
    elif (path / "pnpm-lock.yaml").exists():
        return "pnpm"
    elif (path / "bun.lockb").exists():
        return "bun"
    else:
        return "npm"


def get_project_summary(info: ProjectInfo) -> Dict[str, Any]:
    """
    Convert ProjectInfo to dictionary format.
    
    Args:
        info: ProjectInfo object
    
    Returns:
        Dict with project information
    
    Example:
        >>> info = detect_project(".")
        >>> summary = get_project_summary(info)
        >>> summary['type']
        'react'
    """
    return {
        "type": info.type,
        "framework": info.framework,
        "build_command": info.build_command,
        "output_dir": info.output_dir,
        "package_manager": info.package_manager,
        "detected_files": info.detected_files
    }
