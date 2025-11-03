"""
Environment checking utilities.

Handles detection and resolution of package conflicts and environment issues.
"""
import sys
import subprocess

def check_environment():
    """Check for conflicting packages that cause import errors."""
    try:
        import asyncio
        # Check if asyncio is from site-packages (third-party conflict)
        if hasattr(asyncio, '__file__') and 'site-packages' in str(asyncio.__file__):
            print("⚠️  Warning: Conflicting 'asyncio' package detected", file=sys.stderr)
            print("   Attempting to auto-fix...", file=sys.stderr)
            try:
                subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "asyncio"], 
                             capture_output=True, check=True)
                print("✅ Conflicting package removed. Please run deployx again.", file=sys.stderr)
            except Exception:
                print("\n❌ Auto-fix failed. Please manually run:", file=sys.stderr)
                print("   pip uninstall asyncio", file=sys.stderr)
            sys.exit(1)
    except SyntaxError:
        print("❌ Error: Corrupted asyncio module detected", file=sys.stderr)
        print("   Attempting to fix...", file=sys.stderr)
        try:
            subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "asyncio"], 
                         capture_output=True, check=True)
            print("✅ Fixed. Please run deployx again.", file=sys.stderr)
        except Exception:
            print("   Manual fix required: pip uninstall asyncio", file=sys.stderr)
        sys.exit(1)
    except Exception:
        pass
