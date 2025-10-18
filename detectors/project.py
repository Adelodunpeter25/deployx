import json
from pathlib import Path
from typing import Dict, Any, Optional, List

class ProjectInfo:
    def __init__(self):
        self.type: str = "unknown"
        self.framework: Optional[str] = None
        self.build_command: Optional[str] = None
        self.output_dir: str = "."
        self.package_manager: str = "npm"
        self.detected_files: List[str] = []

def detect_project(project_path: str = ".") -> ProjectInfo:
    """Detect project type, framework, and build settings"""
    path = Path(project_path)
    info = ProjectInfo()
    
    # Check for different project types
    if (path / "package.json").exists():
        info = _detect_nodejs_project(path)
    elif any((path / f).exists() for f in ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"]):
        info = _detect_python_project(path)
    elif (path / "index.html").exists():
        info.type = "static"
        info.output_dir = "."
        info.detected_files.append("index.html")
    elif (path / "public" / "index.html").exists():
        info.type = "static"
        info.output_dir = "public"
        info.detected_files.append("public/index.html")
    
    return info

def _detect_nodejs_project(path: Path) -> ProjectInfo:
    """Detect Node.js project details"""
    info = ProjectInfo()
    info.type = "nodejs"
    info.detected_files.append("package.json")
    
    try:
        with open(path / "package.json", 'r') as f:
            package_json = json.load(f)
        
        # Detect framework from dependencies
        deps = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
        
        # Check for Vite projects first
        if "vite" in deps:
            info = _detect_vite_project(path, deps, package_json)
        elif "react" in deps:
            info.framework = "react"
            info.type = "react"
            info.output_dir = "build"
        elif "next" in deps:
            info.framework = "nextjs"
            info.type = "nextjs"
            info.output_dir = "out"
        elif "vue" in deps:
            info.framework = "vue"
            info.type = "vue"
            info.output_dir = "dist"
        elif "@angular/core" in deps:
            info.framework = "angular"
            info.type = "angular"
            info.output_dir = "dist"
        elif "express" in deps:
            info.framework = "express"
            info.type = "nodejs"
            info.output_dir = "."
        
        # Detect build command
        scripts = package_json.get("scripts", {})
        if "build" in scripts:
            info.build_command = _detect_package_manager(path) + " run build"
        
        # Detect package manager
        info.package_manager = _detect_package_manager(path)
        info.detected_files.append("package.json")
        
    except (json.JSONDecodeError, FileNotFoundError):
        pass
    
    return info

def _detect_vite_project(path: Path, deps: Dict, package_json: Dict) -> ProjectInfo:
    """Detect Vite-based projects"""
    info = ProjectInfo()
    info.framework = "vite"
    info.output_dir = "dist"
    info.detected_files.extend(["package.json"])
    
    # Check for Vite config files
    vite_configs = ["vite.config.js", "vite.config.ts", "vite.config.mjs"]
    for config in vite_configs:
        if (path / config).exists():
            info.detected_files.append(config)
            break
    
    # Determine specific framework with Vite
    if "react" in deps:
        info.type = "react"
        info.framework = "react-vite"
    elif "vue" in deps:
        info.type = "vue"
        info.framework = "vue-vite"
    else:
        info.type = "vite"
    
    return info

def _detect_python_project(path: Path) -> ProjectInfo:
    """Detect Python project details"""
    info = ProjectInfo()
    info.type = "python"
    info.package_manager = _detect_python_package_manager(path)
    
    # Check for Python files that indicate framework
    python_files = list(path.glob("*.py")) + list(path.glob("**/*.py"))
    
    # Read requirements or dependencies to detect framework
    requirements = _read_python_requirements(path)
    
    if "django" in requirements:
        info.framework = "django"
        info.type = "django"
        info.build_command = "python manage.py collectstatic --noinput"
        info.output_dir = "staticfiles"
    elif "flask" in requirements:
        info.framework = "flask"
        info.type = "flask"
        info.output_dir = "."
    elif "fastapi" in requirements:
        info.framework = "fastapi"
        info.type = "fastapi"
        info.output_dir = "."
    
    # Add detected files
    for file in ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"]:
        if (path / file).exists():
            info.detected_files.append(file)
    
    return info

def _read_python_requirements(path: Path) -> List[str]:
    """Read Python requirements from various files"""
    requirements = []
    
    # Check requirements.txt
    if (path / "requirements.txt").exists():
        try:
            with open(path / "requirements.txt", 'r') as f:
                requirements.extend([line.split('==')[0].split('>=')[0].split('<=')[0].strip() 
                                   for line in f if line.strip() and not line.startswith('#')])
        except:
            pass
    
    # Check pyproject.toml
    if (path / "pyproject.toml").exists():
        try:
            import tomllib
            with open(path / "pyproject.toml", 'rb') as f:
                data = tomllib.load(f)
                deps = data.get('project', {}).get('dependencies', [])
                requirements.extend([dep.split('==')[0].split('>=')[0].split('<=')[0].strip() for dep in deps])
        except:
            pass
    
    return [req.lower() for req in requirements]

def _detect_python_package_manager(path: Path) -> str:
    """Detect Python package manager"""
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
    """Detect which Node.js package manager is being used"""
    if (path / "yarn.lock").exists():
        return "yarn"
    elif (path / "pnpm-lock.yaml").exists():
        return "pnpm"
    elif (path / "bun.lockb").exists():
        return "bun"
    else:
        return "npm"

def get_project_summary(info: ProjectInfo) -> Dict[str, Any]:
    """Get project detection summary"""
    return {
        "type": info.type,
        "framework": info.framework,
        "build_command": info.build_command,
        "output_dir": info.output_dir,
        "package_manager": info.package_manager,
        "detected_files": info.detected_files
    }