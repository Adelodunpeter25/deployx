"""
User interface utilities for DeployX.

This module provides rich terminal UI components including progress indicators,
status messages, spinners, and interactive prompts. Uses the Rich library
for enhanced terminal output with colors, animations, and formatting.
"""
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.prompt import Confirm
from contextlib import contextmanager
import time
import subprocess

console = Console()

def success(message: str, celebrate: bool = False) -> None:
    """
    Display success message with green checkmark.
    
    Args:
        message: Success message to display
        celebrate: Show celebration animation if True
    """
    if celebrate:
        _show_celebration(message)
    else:
        console.print(f"✓ {message}", style="bold green")

def _show_celebration(message: str) -> None:
    """
    Show celebratory animation for major successes.
    
    Args:
        message: Success message to display with animation
    """
    # Celebration emojis animation
    celebration_frames = [
        "🎉 🎊 🚀",
        "🎊 🎉 🚀", 
        "🚀 🎉 🎊",
        "🎉 🚀 🎊",
        "🎊 🚀 🎉"
    ]
    
    # Animate celebration
    for frame in celebration_frames:
        console.clear()
        celebration_text = Text(f"\n{frame} SUCCESS! {frame}\n", style="bold green")
        console.print(Align.center(celebration_text))
        console.print(Align.center(Text(message, style="bold white")))
        time.sleep(0.3)
    
    # Final success message
    console.clear()
    console.print(f"\n🎉 {message}", style="bold green")
    console.print("🌟 " + "─" * 50 + " 🌟", style="yellow")

def error(message: str, error_type: str = "general") -> None:
    """
    Display error message with enhanced styling and icons.
    
    Args:
        message: Error message to display
        error_type: Type of error for appropriate icon selection
    """
    error_icons = {
        "auth": "🔐",
        "network": "🌐", 
        "build": "🔨",
        "config": "⚙️",
        "git": "📝",
        "general": "❌"
    }
    
    icon = error_icons.get(error_type, "❌")
    console.print(f"{icon} {message}", style="bold red")
    
    # Add error border for critical errors
    if error_type in ["auth", "config"]:
        console.print("🚨 " + "─" * 50 + " 🚨", style="red")

def info(message: str) -> None:
    """
    Display info message with blue info icon.
    
    Args:
        message: Information message to display
    """
    console.print(f"ℹ {message}", style="bold blue")

def warning(message: str) -> None:
    """
    Display warning message with yellow warning icon.
    
    Args:
        message: Warning message to display
    """
    console.print(f"⚠ {message}", style="bold yellow")

def header(title: str) -> None:
    """
    Display header with ASCII art and command title.
    
    Args:
        title: Title to display in the header panel
    """
    # Always show ASCII art first
    ascii_art = """
██████╗ ███████╗██████╗ ██╗      ██████╗ ██╗   ██╗██╗  ██╗
██╔══██╗██╔════╝██╔══██╗██║     ██╔═══██╗╚██╗ ██╔╝╚██╗██╔╝
██║  ██║█████╗  ██████╔╝██║     ██║   ██║ ╚████╔╝  ╚███╔╝ 
██║  ██║██╔══╝  ██╔═══╝ ██║     ██║   ██║  ╚██╔╝   ██╔██╗ 
██████╔╝███████╗██║     ███████╗╚██████╔╝   ██║   ██╔╝ ██╗
╚═════╝ ╚══════╝╚═╝     ╚══════╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝
"""
    console.print(ascii_art, style="bold cyan")
    console.print(Panel(f"🚀 {title}", style="bold cyan"))

@contextmanager
def spinner(message: str, platform: str = "general"):
    """
    Context manager for loading spinner with platform styling.
    
    Args:
        message: Message to display with spinner
        platform: Platform name for styling
    """
    style = get_platform_style(platform)
    with console.status(f"[{style}]{message}...[/{style}]"):
        yield

def progress_bar(description: str = "Processing"):
    """
    Create progress bar for deployments.
    
    Args:
        description: Description text for the progress bar
        
    Returns:
        Rich Progress instance
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    )

def build_progress_tracker():
    """Create enhanced progress tracker for builds"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(complete_style="green", finished_style="bold green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("•"),
        TextColumn("[bold blue]{task.fields[status]}"),
        console=console
    )

@contextmanager
def build_spinner(command: str, platform: str = "general"):
    """Enhanced spinner for build operations with platform styling"""
    style = get_platform_style(platform)
    
    build_steps = [
        "Installing dependencies...",
        "Running build command...", 
        "Optimizing assets...",
        "Preparing deployment..."
    ]
    
    with console.status("") as status:
        for i, step in enumerate(build_steps):
            progress = int((i + 1) / len(build_steps) * 100)
            status.update(f"[{style}]{step} ({progress}%)[/{style}]")
            time.sleep(0.5)  # Simulate build time
        yield

def print_url(label: str, url: str) -> None:
    """Print URL with special formatting"""
    console.print(f"{label}: [link={url}]{url}[/link]", style="bold")

def print_config_summary(config: dict) -> None:
    """Print configuration summary with platform branding"""
    project = config.get("project", {})
    platform = config.get("platform", "unknown")
    
    platform_style = get_platform_style(platform)
    
    console.print("\n📋 Configuration Summary:", style="bold")
    console.print(f"   Project: {project.get('name', 'N/A')}")
    console.print(f"   Type: {project.get('type', 'N/A')}")
    console.print(f"   Platform: {platform}", style=platform_style)
    console.print()

def get_platform_style(platform: str) -> str:
    """Get platform-specific styling"""
    platform_styles = {
        "github": "bold green",      # GitHub green
        "vercel": "bold white",      # Vercel black/white
        "netlify": "bold cyan",      # Netlify teal
        "railway": "bold magenta",   # Railway purple
        "render": "bold blue",       # Render blue
    }
    return platform_styles.get(platform, "bold white")

def smart_error_recovery(error_message: str, error_type: str = "build") -> bool:
    """Interactive error resolution with suggested fixes"""
    console.print(f"\n❌ {error_message}", style="bold red")
    
    # Define error patterns and fixes
    error_fixes = {
        "react-scripts": [
            ("Run 'npm install' to install dependencies", "npm install"),
            ("Check package.json for missing scripts", None),
            ("Verify Node.js version compatibility", "node --version")
        ],
        "command not found": [
            ("Install missing package manager", None),
            ("Check PATH environment variable", "echo $PATH"),
            ("Verify installation directory", None)
        ],
        "permission denied": [
            ("Fix file permissions", "chmod +x"),
            ("Run with sudo (if needed)", None),
            ("Check directory ownership", "ls -la")
        ],
        "network": [
            ("Check internet connection", "ping google.com"),
            ("Verify proxy settings", None),
            ("Try again in a few minutes", None)
        ]
    }
    
    # Find matching error pattern
    fixes = None
    for pattern, pattern_fixes in error_fixes.items():
        if pattern.lower() in error_message.lower():
            fixes = pattern_fixes
            break
    
    if not fixes:
        fixes = [("Check the error message above for clues", None)]
    
    console.print("\n🔧 Suggested fixes:", style="bold yellow")
    for i, (description, command) in enumerate(fixes, 1):
        console.print(f"  {i}. {description}")
    
    # Ask user if they want to try automatic fixes
    for i, (description, command) in enumerate(fixes, 1):
        if command:
            if Confirm.ask(f"\nWould you like me to try fix #{i}?"):
                try:
                    console.print(f"\n🔄 Running: {command}", style="bold blue")
                    result = subprocess.run(command, shell=True, capture_output=True, text=True)
                    if result.returncode == 0:
                        success(f"Fix #{i} completed successfully")
                        return True
                    else:
                        error(f"Fix #{i} failed: {result.stderr.strip()}")
                except Exception as e:
                    error(f"Failed to run fix #{i}: {str(e)}")
    
    return False

def platform_selection_wizard() -> str:
    """Visual platform selection wizard with feature comparison"""
    import questionary
    
    platforms = [
        {
            "name": "GitHub Pages",
            "features": "Free, 1GB, Custom domains",
            "icon": "🐙",
            "key": "github"
        },
        {
            "name": "Vercel", 
            "features": "Free, Fast CDN, Serverless",
            "icon": "▲",
            "key": "vercel"
        },
        {
            "name": "Netlify",
            "features": "Free, Form handling, CMS",
            "icon": "🌐",
            "key": "netlify"
        },
        {
            "name": "Railway",
            "features": "Free tier, Database support",
            "icon": "🚄",
            "key": "railway"
        },
        {
            "name": "Render",
            "features": "Free tier, Auto-deploy",
            "icon": "🖥️",
            "key": "render"
        }
    ]
    
    choices = [f"{p['name']} - {p['features']}" for p in platforms]
    
    selection = questionary.select(
        "🎯 Select platform:",
        choices=choices
    ).ask()
    
    if not selection:
        return ""
    
    # Find selected platform
    for i, choice in enumerate(choices):
        if choice == selection:
            selected = platforms[i]
            console.print(f"\n✅ Selected: {selected['icon']} {selected['name']}", 
                         style=get_platform_style(selected['key']))
            return selected['key']
    
    return ""