import unittest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from commands.init import init_command
from commands.deploy import deploy_command
from commands.status import status_command
from utils.config import Config
from platforms.base import DeploymentResult, DeploymentStatus

class TestIntegration(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir)
        
        # Create a mock React project
        self._create_mock_react_project()
        
        # Set environment variable
        os.environ['GITHUB_TOKEN'] = 'fake_token_123'
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        if 'GITHUB_TOKEN' in os.environ:
            del os.environ['GITHUB_TOKEN']
    
    def _create_mock_react_project(self):
        """Create a mock React project structure"""
        # package.json
        package_json = {
            "name": "test-react-app",
            "dependencies": {"react": "^18.0.0"},
            "scripts": {"build": "react-scripts build"}
        }
        with open(self.project_path / "package.json", "w") as f:
            json.dump(package_json, f)
        
        # Build output
        build_dir = self.project_path / "build"
        build_dir.mkdir()
        (build_dir / "index.html").write_text("<html><body>React App</body></html>")
        (build_dir / "static").mkdir()
        (build_dir / "static" / "js").mkdir()
        (build_dir / "static" / "js" / "main.js").write_text("console.log('React');")
    
    @patch('commands.init.questionary.confirm')
    @patch('commands.init.questionary.select')
    @patch('commands.init.questionary.text')
    def test_full_init_flow(self, mock_text, mock_select, mock_confirm):
        """Test complete initialization flow"""
        # Mock user inputs
        mock_confirm.return_value.ask.return_value = True
        mock_select.return_value.ask.return_value = "github"
        mock_text.return_value.ask.side_effect = [
            "GITHUB_TOKEN",  # token env
            "testuser/testrepo",  # repo name
            "gh-pages",  # branch
            "npm run build",  # build command
            "build"  # output dir
        ]
        
        result = init_command(str(self.project_path))
        
        self.assertTrue(result)
        
        # Verify config file was created
        config = Config(str(self.project_path))
        self.assertTrue(config.exists())
        
        # Verify config content
        config_data = config.load()
        self.assertEqual(config_data['project']['name'], 'test-react-app')
        self.assertEqual(config_data['project']['type'], 'react')
        self.assertEqual(config_data['platform'], 'github')
        self.assertEqual(config_data['github']['repo'], 'testuser/testrepo')
    
    @patch('commands.deploy.get_platform')
    @patch('commands.deploy.questionary.confirm')
    def test_full_deploy_flow(self, mock_confirm, mock_get_platform):
        """Test complete deployment flow"""
        # Create config first
        config_data = {
            'project': {'name': 'test-app', 'type': 'react'},
            'build': {'command': 'npm run build', 'output': 'build'},
            'platform': 'github',
            'github': {'repo': 'testuser/testrepo', 'method': 'branch', 'branch': 'gh-pages'}
        }
        config = Config(str(self.project_path))
        config.save(config_data)
        
        # Mock user confirmation
        mock_confirm.return_value.ask.side_effect = [True, False]  # Deploy: Yes, Browser: No
        
        # Mock platform
        mock_platform = Mock()
        mock_platform.validate_credentials.return_value = (True, "Valid")
        mock_platform.prepare_deployment.return_value = (True, "5 files ready")
        mock_platform.execute_deployment.return_value = DeploymentResult(
            True, 
            url="https://testuser.github.io/testrepo",
            deployment_id="abc123"
        )
        mock_get_platform.return_value = mock_platform
        
        result = deploy_command(str(self.project_path))
        
        self.assertTrue(result)
        mock_platform.validate_credentials.assert_called_once()
        mock_platform.prepare_deployment.assert_called_once()
        mock_platform.execute_deployment.assert_called_once()
    
    @patch('commands.status.get_platform')
    def test_full_status_flow(self, mock_get_platform):
        """Test complete status checking flow"""
        # Create config
        config_data = {
            'project': {'name': 'test-app', 'type': 'react'},
            'platform': 'github',
            'github': {'repo': 'testuser/testrepo', 'method': 'branch', 'branch': 'gh-pages'}
        }
        config = Config(str(self.project_path))
        config.save(config_data)
        
        # Mock platform
        mock_platform = Mock()
        mock_platform.validate_credentials.return_value = (True, "Valid")
        mock_platform.get_status.return_value = DeploymentStatus(
            status="ready",
            url="https://testuser.github.io/testrepo",
            last_updated="2024-01-15T10:30:00Z",
            message="Deployment ready"
        )
        mock_platform.get_url.return_value = "https://testuser.github.io/testrepo"
        mock_get_platform.return_value = mock_platform
        
        result = status_command(str(self.project_path))
        
        self.assertTrue(result)
        mock_platform.validate_credentials.assert_called_once()
        mock_platform.get_status.assert_called_once()

class TestErrorScenarios(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_init_no_project_files(self):
        """Test init with empty directory"""
        result = init_command(str(self.project_path))
        # Should still work, just detect as unknown project
        # Implementation depends on how we handle unknown projects
    
    def test_deploy_no_config(self):
        """Test deploy without configuration"""
        result = deploy_command(str(self.project_path))
        self.assertFalse(result)
    
    def test_deploy_invalid_config(self):
        """Test deploy with invalid configuration"""
        config = Config(str(self.project_path))
        config.save({"invalid": "config"})
        
        result = deploy_command(str(self.project_path))
        self.assertFalse(result)
    
    def test_status_no_config(self):
        """Test status without configuration"""
        result = status_command(str(self.project_path))
        self.assertFalse(result)
    
    @patch('commands.deploy.get_platform')
    @patch('commands.deploy.questionary.confirm')
    def test_deploy_auth_failure(self, mock_confirm, mock_get_platform):
        """Test deployment with authentication failure"""
        # Create valid config
        config_data = {
            'project': {'name': 'test-app', 'type': 'react'},
            'build': {'output': 'build'},
            'platform': 'github',
            'github': {'repo': 'testuser/testrepo'}
        }
        config = Config(str(self.project_path))
        config.save(config_data)
        
        # Create build output
        build_dir = self.project_path / "build"
        build_dir.mkdir()
        (build_dir / "index.html").write_text("<html></html>")
        
        mock_confirm.return_value.ask.return_value = True
        
        # Mock platform with auth failure
        mock_platform = Mock()
        mock_platform.validate_credentials.return_value = (False, "Invalid token")
        mock_get_platform.return_value = mock_platform
        
        result = deploy_command(str(self.project_path))
        self.assertFalse(result)
    
    @patch('commands.deploy.get_platform')
    @patch('commands.deploy.questionary.confirm')
    def test_deploy_build_failure(self, mock_confirm, mock_get_platform):
        """Test deployment with build failure"""
        config_data = {
            'project': {'name': 'test-app', 'type': 'react'},
            'build': {'command': 'npm run build', 'output': 'build'},
            'platform': 'github',
            'github': {'repo': 'testuser/testrepo'}
        }
        config = Config(str(self.project_path))
        config.save(config_data)
        
        mock_confirm.return_value.ask.return_value = True
        
        # Mock platform with build failure
        mock_platform = Mock()
        mock_platform.validate_credentials.return_value = (True, "Valid")
        mock_platform.prepare_deployment.return_value = (False, "Build failed")
        mock_get_platform.return_value = mock_platform
        
        result = deploy_command(str(self.project_path))
        self.assertFalse(result)

class TestEdgeCases(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_empty_repository(self):
        """Test with empty git repository"""
        # Initialize empty git repo
        import subprocess
        subprocess.run(['git', 'init'], cwd=self.project_path, capture_output=True)
        
        # Should handle gracefully
        from detectors.project import detect_project
        info = detect_project(str(self.project_path))
        # Should not crash
    
    def test_no_build_output(self):
        """Test when build produces no output"""
        # Create package.json but no build output
        package_json = {
            "name": "test-app",
            "dependencies": {"react": "^18.0.0"},
            "scripts": {"build": "echo 'fake build'"}
        }
        with open(self.project_path / "package.json", "w") as f:
            json.dump(package_json, f)
        
        from detectors.project import detect_project
        info = detect_project(str(self.project_path))
        # Should detect project type but handle missing build output
    
    def test_corrupted_config_file(self):
        """Test with corrupted configuration file"""
        config_path = self.project_path / "deployx.yml"
        config_path.write_text("invalid: yaml: content: [")
        
        config = Config(str(self.project_path))
        # Should handle YAML parsing errors gracefully
        try:
            data = config.load()
            # Should return empty dict or handle error
        except Exception:
            # Should not crash the application
            pass

if __name__ == '__main__':
    unittest.main()