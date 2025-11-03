"""
Base command class for CLI commands.

Provides common functionality for error handling, logging, and async execution.
"""
import sys
import asyncio
import traceback
from typing import Callable, Any
import click
from core.logging import get_logger
from utils.ui import error
from utils.errors import DeployXError, display_error_with_suggestions

class BaseCommand:
    """Base class for CLI commands with common error handling."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"cli.{name}")
    
    def handle_async(self, async_func: Callable, *args, **kwargs):
        """Handle async function execution with error handling."""
        try:
            return asyncio.run(async_func(*args, **kwargs))
        except KeyboardInterrupt:
            error(f"\n❌ {self.name.title()} cancelled by user")
            sys.exit(1)
        except DeployXError as e:
            display_error_with_suggestions(e)
            sys.exit(1)
        except Exception as e:
            ctx = click.get_current_context()
            if ctx.obj and ctx.obj.get('verbose'):
                error(f"❌ {self.name.title()} failed: {str(e)}")
                error("Full traceback:")
                traceback.print_exc()
            else:
                error(f"❌ {self.name.title()} failed: {str(e)}")
                error("Use --verbose for detailed error information")
            sys.exit(1)
    
    def handle_sync(self, sync_func: Callable, *args, **kwargs):
        """Handle sync function execution with error handling."""
        try:
            return sync_func(*args, **kwargs)
        except KeyboardInterrupt:
            error(f"\n❌ {self.name.title()} cancelled by user")
            sys.exit(1)
        except DeployXError as e:
            display_error_with_suggestions(e)
            sys.exit(1)
        except Exception as e:
            ctx = click.get_current_context()
            if ctx.obj and ctx.obj.get('verbose'):
                error(f"❌ {self.name.title()} failed: {str(e)}")
                error("Full traceback:")
                traceback.print_exc()
            else:
                error(f"❌ {self.name.title()} failed: {str(e)}")
                error("Use --verbose for detailed error information")
            sys.exit(1)
