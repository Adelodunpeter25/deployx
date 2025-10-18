import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detectors.project import detect_project, get_project_summary
from utils.config import Config, create_default_config

class TestProjectDetection(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.project_path = "."
    
    def test_detect_current_project(self):
        """Test detection on current DeployX project"""
        project_info = detect_project(self.project_path)
        summary = get_project_summary(project_info)
        
        # Should detect Python project with uv
        self.assertEqual(summary['type'], 'python')
        self.assertEqual(summary['package_manager'], 'uv')
        self.assertIn('pyproject.toml', summary['detected_files'])
    
    def test_config_creation(self):
        """Test configuration creation"""
        config_data = create_default_config("test-project", "python", "github")
        
        self.assertEqual(config_data['project']['name'], "test-project")
        self.assertEqual(config_data['project']['type'], "python")
        self.assertEqual(config_data['platform'], "github")
        self.assertIn('github', config_data)
    
    def test_config_manager(self):
        """Test configuration manager"""
        config = Config()
        
        # Test config doesn't exist initially
        self.assertFalse(config.exists())
        
        # Test default values
        self.assertEqual(config.get('nonexistent', 'default'), 'default')

if __name__ == '__main__':
    unittest.main()