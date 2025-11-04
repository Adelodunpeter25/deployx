#!/usr/bin/env python3
"""
Comprehensive test runner for DeployX application.
"""
import sys
import subprocess
import os
from pathlib import Path

def run_tests():
    """Run all tests with comprehensive coverage using uv."""
    print("🧪 Running DeployX Test Suite (with uv)")
    print("=" * 50)
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Test files to run
    test_files = [
        'tests/test_api_integrations.py',
        'tests/test_full_application.py',
        'tests/test_phase2_features.py'
    ]
    
    # Run each test file using uv
    total_passed = 0
    total_failed = 0
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"\n📋 Running {test_file}")
            print("-" * 30)
            
            try:
                result = subprocess.run([
                    'uv', 'run', 'pytest', 
                    test_file, '-v', '--tb=short'
                ], capture_output=True, text=True)
                
                print(result.stdout)
                if result.stderr:
                    print("STDERR:", result.stderr)
                
                if result.returncode == 0:
                    print(f"✅ {test_file} - PASSED")
                    total_passed += 1
                else:
                    print(f"❌ {test_file} - FAILED")
                    total_failed += 1
                    
            except Exception as e:
                print(f"❌ Error running {test_file}: {e}")
                total_failed += 1
        else:
            print(f"⚠️ Test file not found: {test_file}")
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    print(f"📊 Total: {total_passed + total_failed}")
    
    if total_failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"\n💥 {total_failed} TEST(S) FAILED!")
        return False

def check_test_environment():
    """Check if test environment is properly set up with uv."""
    print("🔍 Checking test environment (uv)...")
    
    # Check if uv is available
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ uv available: {result.stdout.strip()}")
        else:
            print("❌ uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh")
            return False
    except FileNotFoundError:
        print("❌ uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh")
        return False
    
    # Check if pytest is available in uv environment
    try:
        result = subprocess.run(['uv', 'run', 'python', '-c', 'import pytest; print("pytest available")'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ pytest available in uv environment")
        else:
            print("❌ pytest not found. Install with: uv add pytest")
            return False
    except Exception as e:
        print(f"❌ Error checking pytest: {e}")
        return False
    
    # Check if project modules can be imported
    try:
        result = subprocess.run([
            'uv', 'run', 'python', '-c', 
            'from cli.factory import create_cli; from platforms.factory import PlatformFactory; print("Project modules importable")'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Project modules importable")
        else:
            print(f"❌ Import error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error checking imports: {e}")
        return False
    
    print("✅ Test environment ready")
    return True

def run_quick_test():
    """Run a quick smoke test."""
    print("🚀 Running quick smoke test...")
    
    try:
        result = subprocess.run([
            'uv', 'run', 'python', '-c', '''
import sys
sys.path.insert(0, ".")
from cli.factory import create_cli
from platforms.factory import PlatformFactory

# Test CLI creation
cli = create_cli("0.8.0")
print("✅ CLI creation works")

# Test platform factory
platforms = PlatformFactory.get_available_platforms()
print(f"✅ Platform factory works: {len(platforms)} platforms")

# Test imports
from commands.auth import auth_status_command
print("✅ Auth commands import")

print("🎉 Smoke test passed!")
'''
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f"❌ Smoke test failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running smoke test: {e}")
        return False

if __name__ == '__main__':
    if not check_test_environment():
        print("\n💡 To set up the test environment:")
        print("   uv add pytest")
        print("   uv sync")
        sys.exit(1)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        success = run_quick_test()
    else:
        success = run_tests()
    
    sys.exit(0 if success else 1)
