"""
CLI factory for building the main CLI application.

Constructs the Click CLI with all commands and configuration.
"""
import click
from core.logging import setup_logging, get_logger
from utils.ui import info
from .commands import (
    init, deploy, status, interactive, logs, config, 
    history, rollback, version_cmd
)

def create_cli(version: str):
    """
    Create the main CLI application.
    
    Args:
        version: Application version string
        
    Returns:
        Click CLI group with all commands
    """
    
    @click.group()
    @click.version_option(version=version, prog_name="DeployX")
    @click.option('--verbose', '-v', is_flag=True, help='Enable verbose output for debugging')
    @click.option('--log-file', help='Log file path')
    @click.pass_context
    def cli(ctx, verbose, log_file):
        """
        🚀 DeployX - One CLI for all your deployments
        
        Stop memorizing platform-specific commands. Deploy to GitHub Pages, 
        Vercel, Netlify, Railway, and Render with zero configuration.
        
        Get started:
          1. Run 'deployx init' in your project directory
          2. Follow the interactive setup wizard
          3. Deploy with 'deployx deploy'
        
        Documentation: https://github.com/Adelodunpeter25/deployx
        """
        # Ensure context object exists
        ctx.ensure_object(dict)
        ctx.obj['verbose'] = verbose
        ctx.obj['log_file'] = log_file
        
        # Setup logging
        logger = setup_logging(verbose=verbose, log_file=log_file)
        
        if verbose:
            info(f"DeployX v{version} - Verbose mode enabled")
            logger.info(f"DeployX v{version} started with verbose logging")
    
    # Add all commands
    cli.add_command(init)
    cli.add_command(deploy)
    cli.add_command(status)
    cli.add_command(interactive)
    cli.add_command(logs)
    cli.add_command(config)
    cli.add_command(history)
    cli.add_command(rollback)
    cli.add_command(version_cmd)
    
    return cli
