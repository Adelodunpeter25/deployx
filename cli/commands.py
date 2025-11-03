"""
CLI command implementations.

Contains all Click command definitions with simplified error handling.
"""
import sys
import click
from pathlib import Path
from .base import BaseCommand
from core.logging import get_logger
from core.services import DeploymentService, InitService, StatusService
from commands.logs import logs_command
from commands.config import config_show_command, config_edit_command, config_validate_command
from commands.history import history_command
from commands.rollback import rollback_command
from commands.interactive import interactive_command
from utils.ui import header, error, info
from platforms.factory import PlatformFactory

# Command instances
init_cmd = BaseCommand("init")
deploy_cmd = BaseCommand("deploy")
status_cmd = BaseCommand("status")

@click.command()
@click.option('--path', '-p', default='.', help='Project path')
@click.pass_context
def init(ctx, path):
    """Initialize deployment configuration for your project."""
    
    async def run_init():
        service = InitService(path)
        success, message = await service.initialize_project()
        
        if success:
            info(f"✅ {message}")
            return True
        else:
            error(f"❌ {message}")
            return False
    
    success = init_cmd.handle_async(run_init)
    sys.exit(0 if success else 1)

@click.command()
@click.option('--path', '-p', default='.', help='Project path')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation prompts')
@click.option('--dry-run', is_flag=True, help='Show what would happen without deploying')
@click.pass_context
def deploy(ctx, path, force, dry_run):
    """Deploy your project to the configured platform."""
    
    async def run_deploy():
        service = DeploymentService(path)
        success, message = await service.deploy(force=force, dry_run=dry_run)
        
        if success:
            info(f"✅ {message}")
            return True
        else:
            error(f"❌ {message}")
            return False
    
    success = deploy_cmd.handle_async(run_deploy)
    sys.exit(0 if success else 1)

@click.command()
@click.option('--path', '-p', default='.', help='Project path')
@click.option('--quick', '-q', is_flag=True, help='Quick status check')
@click.pass_context
def status(ctx, path, quick):
    """Check deployment status and information."""
    
    async def run_status():
        service = StatusService(path)
        success, message = await service.get_status()
        
        if success:
            if not quick:
                info(f"📊 {message}")
            return True
        else:
            if not quick:
                error(f"❌ {message}")
            return False
    
    success = status_cmd.handle_async(run_status)
    sys.exit(0 if success else 1)

@click.command()
@click.option('--path', '-p', default='.', help='Project path')
@click.pass_context
def interactive(ctx, path):
    """Interactive mode - Complete setup and deployment workflow."""
    
    def run_interactive():
        return interactive_command(path)
    
    cmd = BaseCommand("interactive")
    success = cmd.handle_sync(run_interactive)
    sys.exit(0 if success else 1)

@click.command()
@click.option('--path', '-p', default='.', help='Project path')
@click.option('--follow', '-f', is_flag=True, help='Stream logs in real-time')
@click.option('--tail', '-t', type=int, help='Number of lines to show from end')
@click.pass_context
def logs(ctx, path, follow, tail):
    """View deployment logs."""
    
    def run_logs():
        return logs_command(path, follow=follow, tail=tail)
    
    try:
        cmd = BaseCommand("logs")
        success = cmd.handle_sync(run_logs)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        info("\n📋 Logs viewing cancelled")
        sys.exit(0)

@click.group()
def config():
    """Configuration management commands."""
    pass

@config.command('show')
@click.option('--path', '-p', default='.', help='Project path')
@click.pass_context
def config_show(ctx, path):
    """Show current configuration."""
    
    def run_config_show():
        return config_show_command(path)
    
    cmd = BaseCommand("config-show")
    success = cmd.handle_sync(run_config_show)
    sys.exit(0 if success else 1)

@config.command('edit')
@click.option('--path', '-p', default='.', help='Project path')
@click.pass_context
def config_edit(ctx, path):
    """Edit configuration file."""
    
    def run_config_edit():
        return config_edit_command(path)
    
    cmd = BaseCommand("config-edit")
    success = cmd.handle_sync(run_config_edit)
    sys.exit(0 if success else 1)

@config.command('validate')
@click.option('--path', '-p', default='.', help='Project path')
@click.pass_context
def config_validate(ctx, path):
    """Validate configuration without deploying."""
    
    def run_config_validate():
        return config_validate_command(path)
    
    cmd = BaseCommand("config-validate")
    success = cmd.handle_sync(run_config_validate)
    sys.exit(0 if success else 1)

@click.command()
@click.option('--path', '-p', default='.', help='Project path')
@click.option('--limit', '-l', type=int, help='Number of deployments to show')
@click.pass_context
def history(ctx, path, limit):
    """Show deployment history."""
    
    def run_history():
        return history_command(path, limit=limit)
    
    cmd = BaseCommand("history")
    success = cmd.handle_sync(run_history)
    sys.exit(0 if success else 1)

@click.command()
@click.option('--path', '-p', default='.', help='Project path')
@click.option('--target', '-t', type=int, help='Deployment index to rollback to')
@click.pass_context
def rollback(ctx, path, target):
    """Rollback to a previous deployment."""
    
    def run_rollback():
        return rollback_command(path, target_index=target)
    
    cmd = BaseCommand("rollback")
    success = cmd.handle_sync(run_rollback)
    sys.exit(0 if success else 1)

@click.command(name='version')
@click.pass_context
def version_cmd(ctx):
    """Show version information and system details."""
    __version__ = "0.7.0"  # Define version locally
    
    header(f"DeployX v{__version__}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")
    print(f"Installation: {Path(__file__).parent.parent}")
    
    # Show available platforms
    try:
        platforms = PlatformFactory.get_available_platforms()
        print(f"Available Platforms: {', '.join(platforms)}")
    except Exception:
        print("Available Platforms: Error loading")
