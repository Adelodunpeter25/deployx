from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from contextlib import contextmanager

console = Console()

def success(message: str) -> None:
    """Display success message with green checkmark"""
    console.print(f"✓ {message}", style="bold green")

def error(message: str) -> None:
    """Display error message with red X mark"""
    console.print(f"✗ {message}", style="bold red")

def info(message: str) -> None:
    """Display info message with blue info icon"""
    console.print(f"ℹ {message}", style="bold blue")

def warning(message: str) -> None:
    """Display warning message with yellow warning icon"""
    console.print(f"⚠ {message}", style="bold yellow")

def header(title: str) -> None:
    """Display header with panel"""
    console.print(Panel(f"🚀 {title}", style="bold cyan"))

@contextmanager
def spinner(message: str):
    """Context manager for loading spinner"""
    with console.status(f"[bold blue]{message}..."):
        yield

def progress_bar(description: str = "Processing"):
    """Create progress bar for deployments"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    )

def print_url(label: str, url: str) -> None:
    """Print URL with special formatting"""
    console.print(f"{label}: [link={url}]{url}[/link]", style="bold")

def print_config_summary(config: dict) -> None:
    """Print configuration summary"""
    project = config.get("project", {})
    platform = config.get("platform", "unknown")
    
    console.print("\n📋 Configuration Summary:", style="bold")
    console.print(f"   Project: {project.get('name', 'N/A')}")
    console.print(f"   Type: {project.get('type', 'N/A')}")
    console.print(f"   Platform: {platform}")
    console.print()