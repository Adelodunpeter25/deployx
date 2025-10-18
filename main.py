#!/usr/bin/env python3
"""
DeployX - Deploy Anywhere with One Command
A CLI tool for deploying projects to multiple platforms
"""

import sys
import os
import click
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from commands.init import init_command
from commands.deploy import deploy_command, redeploy_command
from commands.status import status_command, quick_status_command
from utils.ui import header, error, success, info
from utils.errors import DeployXError, display_error_with_suggestions

# Version information
__version__ = "0.1.0"

@click.group()
@click.version_option(version=__version__, prog_name="DeployX")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output for debugging')
@click.pass_context
def cli(ctx, verbose):
    """
    🚀 DeployX - Deploy Anywhere with One Command
    
    A modern CLI tool for deploying web projects to multiple platforms
    including GitHub Pages, Vercel, and Netlify with zero configuration.
    
    Examples:
      deployx init                 # Set up deployment configuration
      deployx deploy               # Deploy your project
      deployx status               # Check deployment status
      deployx deploy --force       # Force redeploy without confirmation
    
    Get started:
      1. Run 'deployx init' in your project directory
      2. Follow the interactive setup wizard
      3. Deploy with 'deployx deploy'
    
    Documentation: https://github.com/deployx/deployx
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    # Set up global error handling
    if verbose:
        info(f"DeployX v{__version__} - Verbose mode enabled")

@cli.command()
@click.option('--path', '-p', default='.', help='Project path (default: current directory)')
@click.pass_context
def init(ctx, path):
    """
    🔧 Initialize deployment configuration for your project.
    
    This command will:
    • Analyze your project structure and detect framework
    • Guide you through platform selection (GitHub Pages, Vercel, Netlify)
    • Configure build settings and deployment options
    • Create a deployx.yml configuration file
    
    Examples:
      deployx init                 # Initialize in current directory
      deployx init --path ./app    # Initialize in specific directory
    """
    try:
        success_result = init_command(path)
        if success_result:
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        error("\n❌ Setup cancelled by user")
        sys.exit(1)
    except DeployXError as e:
        display_error_with_suggestions(e)
        sys.exit(1)
    except Exception as e:
        if ctx.obj.get('verbose'):
            import traceback
            error(f"❌ Initialization failed: {str(e)}")
            error("Full traceback:")
            traceback.print_exc()
        else:
            error(f"❌ Initialization failed: {str(e)}")
            error("Use --verbose for detailed error information")
        sys.exit(1)

@cli.command()
@click.option('--path', '-p', default='.', help='Project path (default: current directory)')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation prompts')
@click.pass_context
def deploy(ctx, path, force):
    """
    🚀 Deploy your project to the configured platform.
    
    This command will:
    • Validate your configuration and credentials
    • Run build commands if configured
    • Deploy files to your chosen platform
    • Provide live URL and deployment status
    
    Examples:
      deployx deploy               # Interactive deployment
      deployx deploy --force       # Skip confirmation prompts
      deployx deploy --path ./app  # Deploy specific directory
    
    Note: Run 'deployx init' first if no configuration exists.
    """
    try:
        if force:
            success_result = redeploy_command(path)
        else:
            success_result = deploy_command(path)
            
        if success_result:
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        error("\n❌ Deployment cancelled by user")
        sys.exit(1)
    except DeployXError as e:
        display_error_with_suggestions(e)
        sys.exit(1)
    except Exception as e:
        if ctx.obj.get('verbose'):
            import traceback
            error(f"❌ Deployment failed: {str(e)}")
            error("Full traceback:")
            traceback.print_exc()
        else:
            error(f"❌ Deployment failed: {str(e)}")
            error("Use --verbose for detailed error information")
        sys.exit(1)

@cli.command()
@click.option('--path', '-p', default='.', help='Project path (default: current directory)')
@click.option('--quick', '-q', is_flag=True, help='Quick status check (returns exit code only)')
@click.pass_context
def status(ctx, path, quick):
    """
    📊 Check deployment status and information.
    
    This command will:
    • Show current deployment status (ready, building, error)
    • Display live URL and last deployment time
    • Provide troubleshooting tips if issues are found
    • Show platform-specific configuration details
    
    Examples:
      deployx status               # Full status information
      deployx status --quick       # Quick check (for CI/CD)
      deployx status --path ./app  # Check specific directory
    
    Exit codes (--quick mode):
      0: Deployment is ready
      1: Deployment has issues
      2: Configuration not found
    """
    try:
        if quick:
            status_result = quick_status_command(path)
            if status_result == 'ready':
                sys.exit(0)
            elif status_result is None:
                sys.exit(2)  # No config
            else:
                sys.exit(1)  # Issues
        else:
            success_result = status_command(path)
            if success_result:
                sys.exit(0)
            else:
                sys.exit(1)
    except KeyboardInterrupt:
        error("\n❌ Status check cancelled by user")
        sys.exit(1)
    except DeployXError as e:
        display_error_with_suggestions(e)
        sys.exit(1)
    except Exception as e:
        if ctx.obj.get('verbose'):
            import traceback
            error(f"❌ Status check failed: {str(e)}")
            error("Full traceback:")
            traceback.print_exc()
        else:
            error(f"❌ Status check failed: {str(e)}")
            error("Use --verbose for detailed error information")
        sys.exit(1)

@cli.command()
@click.pass_context
def version(ctx):
    """
    📋 Show version information and system details.
    """
    header(f"DeployX v{__version__}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")
    print(f"Installation: {Path(__file__).parent}")
    
    # Show available platforms
    try:
        from platforms.factory import PlatformFactory
        platforms = PlatformFactory.get_available_platforms()
        print(f"Available Platforms: {', '.join(platforms)}")
    except:
        print("Available Platforms: Error loading")

def main():
    """
    Main entry point with global exception handling
    """
    try:
        cli()
    except KeyboardInterrupt:
        error("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        error(f"❌ Unexpected error: {str(e)}")
        error("Please report this issue at: https://github.com/deployx/deployx/issues")
        sys.exit(1)

if __name__ == '__main__':
    main()