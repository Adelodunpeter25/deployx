#!/usr/bin/env python3
"""
Test runner for DeployX - runs all test suites
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_all_tests():
    """Run all test suites and generate report"""
    
    print("🧪 Running DeployX Test Suite")
    print("=" * 50)
    
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    if result.skipped:
        print(f"\n⏭️  Skipped: {len(result.skipped)} tests (manual tests)")
    
    # Overall result
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

def run_unit_tests_only():
    """Run only unit tests (excluding integration and manual)"""
    print("🔬 Running Unit Tests Only")
    print("=" * 30)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add specific unit test modules
    unit_test_modules = [
        'test_config',
        'test_project_detection',
        'test_github_platform',
        'test_deploy_command',
        'test_detection'
    ]
    
    for module in unit_test_modules:
        try:
            tests = loader.loadTestsFromName(module)
            suite.addTests(tests)
        except ImportError:
            print(f"⚠️  Could not load {module}")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1

def run_integration_tests_only():
    """Run only integration tests"""
    print("🔗 Running Integration Tests Only")
    print("=" * 35)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('test_integration')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1

def check_test_coverage():
    """Check which components have tests"""
    print("📋 Test Coverage Check")
    print("=" * 25)
    
    components = {
        'Configuration': 'test_config.py',
        'Project Detection': 'test_project_detection.py', 
        'GitHub Platform': 'test_github_platform.py',
        'Deploy Command': 'test_deploy_command.py',
        'Init Command': 'test_detection.py',
        'Integration Tests': 'test_integration.py',
        'Manual Tests': 'test_manual_scenarios.py'
    }
    
    test_dir = Path(__file__).parent
    
    for component, test_file in components.items():
        if (test_dir / test_file).exists():
            print(f"✅ {component}")
        else:
            print(f"❌ {component} - Missing {test_file}")
    
    print(f"\nTest files found: {len([f for f in test_dir.glob('test_*.py')])}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'unit':
            sys.exit(run_unit_tests_only())
        elif command == 'integration':
            sys.exit(run_integration_tests_only())
        elif command == 'coverage':
            check_test_coverage()
            sys.exit(0)
        elif command == 'help':
            print("""
DeployX Test Runner

Usage:
  python run_all_tests.py [command]

Commands:
  (no args)    Run all tests
  unit         Run only unit tests
  integration  Run only integration tests
  coverage     Check test coverage
  help         Show this help

Examples:
  python run_all_tests.py
  python run_all_tests.py unit
  python run_all_tests.py coverage
            """)
            sys.exit(0)
        else:
            print(f"Unknown command: {command}")
            print("Use 'help' for available commands")
            sys.exit(1)
    else:
        sys.exit(run_all_tests())