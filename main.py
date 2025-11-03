#!/usr/bin/env python3
"""
DeployX - One CLI for all your deployments
Stop memorizing platform-specific commands
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.environment import check_environment
from cli.factory import create_cli
from utils.ui import error

# Version information
__version__ = "0.7.0"

def main():
    """Main entry point with global exception handling."""
    # Check environment before doing anything
    check_environment()
    
    try:
        # Create and run CLI
        cli = create_cli(__version__)
        cli()
    except KeyboardInterrupt:
        error("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        error(f"❌ Unexpected error: {str(e)}")
        error("Please report this issue at: https://github.com/Adelodunpeter25/deployx/issues")
        sys.exit(1)

if __name__ == '__main__':
    main()
