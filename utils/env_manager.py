"""
Environment variable management for deployment platforms.

Handles .env file detection, parsing, and user interaction for
configuring environment variables across different platforms.
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import questionary
from utils.ui import info, success, warning, error

class EnvManager:
    """Manages environment variables for deployment platforms."""
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.env_vars: Dict[str, str] = {}
    
    def detect_env_files(self) -> List[Path]:
        """Detect .env files in project directory."""
        env_files = []
        possible_files = [".env", ".env.local", ".env.production", ".env.staging"]
        
        for filename in possible_files:
            env_file = self.project_path / filename
            if env_file.exists():
                env_files.append(env_file)
        
        return env_files
    
    def parse_env_file(self, env_file: Path) -> Dict[str, str]:
        """Parse environment variables from .env file."""
        env_vars = {}
        
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse KEY=VALUE format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        env_vars[key] = value
                    else:
                        warning(f"Skipping invalid line {line_num} in {env_file.name}: {line}")
        
        except Exception as e:
            error(f"Failed to parse {env_file.name}: {str(e)}")
        
        return env_vars
    
    def is_sensitive_variable(self, key: str) -> bool:
        """Check if variable name suggests sensitive content."""
        sensitive_patterns = [
            r'.*secret.*', r'.*key.*', r'.*password.*', r'.*token.*',
            r'.*private.*', r'.*auth.*', r'.*credential.*', r'.*api_key.*'
        ]
        
        key_lower = key.lower()
        return any(re.match(pattern, key_lower) for pattern in sensitive_patterns)
    
    def preview_variable_value(self, value: str, is_sensitive: bool = False) -> str:
        """Create a preview of variable value for display."""
        if not value:
            return "(empty)"
        
        if is_sensitive and len(value) > 6:
            return f"{value[:3]}...***"
        elif len(value) > 50:
            return f"{value[:47]}..."
        else:
            return value
    
    def collect_env_variables(self) -> Dict[str, str]:
        """Main method to collect environment variables from user."""
        info("🔍 Environment Variable Configuration")
        
        # Detect .env files
        env_files = self.detect_env_files()
        
        if env_files:
            return self._handle_env_files(env_files)
        else:
            return self._handle_manual_input()
    
    def _handle_env_files(self, env_files: List[Path]) -> Dict[str, str]:
        """Handle environment variable collection when .env files exist."""
        info(f"📁 Found {len(env_files)} environment file(s): {', '.join(f.name for f in env_files)}")
        
        choices = [
            "Auto-configure from .env file(s)",
            "Paste variables manually",
            "Add variables interactively", 
            "Skip environment setup"
        ]
        
        choice = questionary.select(
            "How would you like to configure environment variables?",
            choices=choices
        ).ask()
        
        if choice == choices[0]:  # Auto-configure from files
            return self._configure_from_files(env_files)
        elif choice == choices[1]:  # Paste manually
            return self._paste_variables()
        elif choice == choices[2]:  # Interactive entry
            return self._interactive_entry()
        else:  # Skip
            return {}
    
    def _handle_manual_input(self) -> Dict[str, str]:
        """Handle environment variable collection when no .env files exist."""
        info("📝 No .env files found")
        
        choices = [
            "Paste variables manually",
            "Add variables interactively",
            "Skip environment setup"
        ]
        
        choice = questionary.select(
            "How would you like to configure environment variables?",
            choices=choices
        ).ask()
        
        if choice == choices[0]:  # Paste manually
            return self._paste_variables()
        elif choice == choices[1]:  # Interactive entry
            return self._interactive_entry()
        else:  # Skip
            return {}
    
    def _configure_from_files(self, env_files: List[Path]) -> Dict[str, str]:
        """Configure variables from .env files."""
        all_vars = {}
        
        # Parse all files
        for env_file in env_files:
            file_vars = self.parse_env_file(env_file)
            all_vars.update(file_vars)
        
        if not all_vars:
            warning("No valid environment variables found in files")
            return {}
        
        # Show preview
        info(f"📋 Found {len(all_vars)} variables:")
        for key, value in all_vars.items():
            is_sensitive = self.is_sensitive_variable(key)
            preview = self.preview_variable_value(value, is_sensitive)
            sensitive_marker = " (sensitive)" if is_sensitive else ""
            print(f"  ✓ {key}={preview}{sensitive_marker}")
        
        # Ask for confirmation
        choices = ["Configure all variables", "Select specific variables", "Cancel"]
        choice = questionary.select(
            f"Configure {len(all_vars)} variables for deployment?",
            choices=choices
        ).ask()
        
        if choice == choices[0]:  # All variables
            return all_vars
        elif choice == choices[1]:  # Select specific
            return self._select_variables(all_vars)
        else:  # Cancel
            return {}
    
    def _select_variables(self, all_vars: Dict[str, str]) -> Dict[str, str]:
        """Allow user to select specific variables."""
        selected_keys = questionary.checkbox(
            "Select variables to configure:",
            choices=[
                questionary.Choice(
                    title=f"{key}={self.preview_variable_value(value, self.is_sensitive_variable(key))}",
                    value=key
                )
                for key, value in all_vars.items()
            ]
        ).ask()
        
        return {key: all_vars[key] for key in selected_keys}
    
    def _paste_variables(self) -> Dict[str, str]:
        """Allow user to paste environment variables."""
        info("📝 Paste environment variables (KEY=VALUE format, one per line)")
        info("Press Enter twice when finished:")
        
        variables = {}
        while True:
            try:
                line = input("> ").strip()
                if not line:
                    break
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    variables[key] = value
                    success(f"Added: {key}")
                else:
                    warning(f"Invalid format: {line} (use KEY=VALUE)")
            
            except KeyboardInterrupt:
                break
        
        return variables
    
    def _interactive_entry(self) -> Dict[str, str]:
        """Interactive environment variable entry."""
        variables = {}
        
        while True:
            key = questionary.text("Variable name (or press Enter to finish):").ask()
            if not key:
                break
            
            value = questionary.password(f"Value for {key}:").ask()
            variables[key] = value
            success(f"Added: {key}")
        
        return variables
