import unittest
import tempfile
import shutil
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import Config, create_default_config
from utils.validator import validate_config

class TestConfig(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config(self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_config_not_exists_initially(self):
        """Test config file doesn't exist initially"""
        self.assertFalse(self.config.exists())
    
    def test_load_empty_config(self):
        """Test loading when no config file exists"""
        data = self.config.load()
        self.assertEqual(data, {})
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration"""
        test_data = {
            'project': {'name': 'test', 'type': 'react'},
            'platform': 'github'
        }
        
        self.config.save(test_data)
        self.assertTrue(self.config.exists())
        
        loaded_data = self.config.load()
        self.assertEqual(loaded_data, test_data)
    
    def test_get_config_value(self):
        """Test getting configuration values"""
        test_data = {'platform': 'github', 'github': {'repo': 'test/repo'}}
        self.config.save(test_data)
        
        self.assertEqual(self.config.get('platform'), 'github')
        self.assertEqual(self.config.get('nonexistent', 'default'), 'default')
    
    def test_get_platform_config(self):
        """Test getting platform-specific configuration"""
        test_data = {'github': {'repo': 'test/repo', 'branch': 'main'}}
        self.config.save(test_data)
        
        github_config = self.config.get_platform_config('github')
        self.assertEqual(github_config['repo'], 'test/repo')
        
        empty_config = self.config.get_platform_config('vercel')
        self.assertEqual(empty_config, {})
    
    def test_create_default_config(self):
        """Test default configuration creation"""
        config = create_default_config('test-app', 'react', 'github')
        
        self.assertEqual(config['project']['name'], 'test-app')
        self.assertEqual(config['project']['type'], 'react')
        self.assertEqual(config['platform'], 'github')
        self.assertEqual(config['build']['command'], 'npm run build')
        self.assertEqual(config['build']['output'], 'build')
        self.assertIn('github', config)

class TestValidator(unittest.TestCase):
    
    def test_valid_config(self):
        """Test validation of valid configuration"""
        config = {
            'project': {'name': 'test', 'type': 'react'},
            'build': {'output': 'build'},
            'platform': 'github',
            'github': {}
        }
        
        errors = validate_config(config)
        self.assertEqual(errors, [])
    
    def test_missing_sections(self):
        """Test validation with missing sections"""
        config = {'project': {'name': 'test'}}
        
        errors = validate_config(config)
        self.assertIn('Missing required section: build', errors)
        self.assertIn('Missing required section: platform', errors)
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields"""
        config = {
            'project': {'name': 'test'},  # missing 'type'
            'build': {},  # missing 'output'
            'platform': 'github'
        }
        
        errors = validate_config(config)
        self.assertIn('Missing required field: project.type', errors)
        self.assertIn('Missing required field: build.output', errors)
    
    def test_unsupported_platform(self):
        """Test validation with unsupported platform"""
        config = {
            'project': {'name': 'test', 'type': 'react'},
            'build': {'output': 'build'},
            'platform': 'unsupported'
        }
        
        errors = validate_config(config)
        self.assertIn('Unsupported platform: unsupported', errors)
    
    def test_unsupported_project_type(self):
        """Test validation with unsupported project type"""
        config = {
            'project': {'name': 'test', 'type': 'unsupported'},
            'build': {'output': 'build'},
            'platform': 'github',
            'github': {}
        }
        
        errors = validate_config(config)
        self.assertIn('Unsupported project type: unsupported', errors)

if __name__ == '__main__':
    unittest.main()