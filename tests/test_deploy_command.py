import unittest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from commands.deploy import deploy_command, redeploy_command, _show_deployment_summary
from utils.config import Config
from platforms.base import DeploymentResult

class TestDeployCommand(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary project directory
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir)
        
        # Create valid configuration
        self.config_data = {
            'project': {
                'name': 'test-project',
                'type': 'react'
            },
            'build': {
                'command': 'npm run build',
                'output': 'build'
            },
            'platform': 'github',
            'github': {
                'repo': 'testuser/testrepo',
                'method': 'branch',
                'branch': 'gh-pages',
                'token_env': 'GITHUB_TOKEN'
            }
        }
        
        # Create config file
        config = Config(str(self.project_path))
        config.save(self.config_data)
        
        # Create build output
        build_dir = self.project_path / 'build'
        build_dir.mkdir()
        (build_dir / 'index.html').write_text('<html><body>Test</body></html>')
        
        # Set environment variable
        os.environ['GITHUB_TOKEN'] = 'fake_token_123'
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
        if 'GITHUB_TOKEN' in os.environ:
            del os.environ['GITHUB_TOKEN']
    
    def test_deploy_no_config(self):
        """Test deploy command without configuration"""
        # Remove config file
        config_path = self.project_path / 'deployx.yml'
        config_path.unlink()
        
        result = deploy_command(str(self.project_path))
        
        self.assertFalse(result)
    
    def test_deploy_invalid_config(self):
        """Test deploy command with invalid configuration"""
        # Create invalid config
        invalid_config = {'invalid': 'config'}
        config = Config(str(self.project_path))
        config.save(invalid_config)
        
        result = deploy_command(str(self.project_path))
        
        self.assertFalse(result)
    
    @patch('commands.deploy.get_platform')
    @patch('commands.deploy.questionary.confirm')
    def test_deploy_platform_initialization_failure(self, mock_confirm, mock_get_platform):
        """Test deploy command when platform initialization fails"""
        mock_confirm.return_value.ask.return_value = True
        mock_get_platform.side_effect = Exception("Platform init failed")
        
        result = deploy_command(str(self.project_path))
        
        self.assertFalse(result)
    
    @patch('commands.deploy.get_platform')
    @patch('commands.deploy.questionary.confirm')
    def test_deploy_credential_validation_failure(self, mock_confirm, mock_get_platform):
        """Test deploy command when credential validation fails"""
        mock_confirm.return_value.ask.return_value = True
        
        # Mock platform with failed validation
        mock_platform = Mock()
        mock_platform.validate_credentials.return_value = (False, "Invalid token")
        mock_get_platform.return_value = mock_platform
        
        result = deploy_command(str(self.project_path))
        
        self.assertFalse(result)
        mock_platform.validate_credentials.assert_called_once()
    
    @patch('commands.deploy.get_platform')
    @patch('commands.deploy.questionary.confirm')
    def test_deploy_preparation_failure(self, mock_confirm, mock_get_platform):
        """Test deploy command when preparation fails"""
        mock_confirm.return_value.ask.return_value = True
        
        # Mock platform with failed preparation
        mock_platform = Mock()
        mock_platform.validate_credentials.return_value = (True, "Valid")
        mock_platform.prepare_deployment.return_value = (False, "Build failed")
        mock_get_platform.return_value = mock_platform
        
        result = deploy_command(str(self.project_path))
        
        self.assertFalse(result)
        mock_platform.prepare_deployment.assert_called_once()
    
    @patch('commands.deploy.get_platform')
    @patch('commands.deploy.questionary.confirm')
    def test_deploy_execution_failure(self, mock_confirm, mock_get_platform):
        """Test deploy command when deployment execution fails"""
        mock_confirm.return_value.ask.return_value = True
        
        # Mock platform with failed deployment
        mock_platform = Mock()
        mock_platform.validate_credentials.return_value = (True, "Valid")
        mock_platform.prepare_deployment.return_value = (True, "Ready")
        mock_platform.execute_deployment.return_value = DeploymentResult(
            False, message="Deployment failed"
        )
        mock_get_platform.return_value = mock_platform
        
        result = deploy_command(str(self.project_path))
        
        self.assertFalse(result)
        mock_platform.execute_deployment.assert_called_once()
    
    @patch('commands.deploy.get_platform')
    @patch('commands.deploy.questionary.confirm')
    @patch('commands.deploy.webbrowser.open')
    def test_deploy_success_full_flow(self, mock_browser, mock_confirm, mock_get_platform):
        """Test successful deployment with full flow"""
        # Mock user confirmations
        mock_question = Mock()
        mock_question.ask.side_effect = [True, False]  # Deploy: Yes, Browser: No
        mock_confirm.return_value = mock_question
        
        # Mock successful platform
        mock_platform = Mock()
        mock_platform.validate_credentials.return_value = (True, "Valid credentials")
        mock_platform.prepare_deployment.return_value = (True, "5 files ready")
        mock_platform.execute_deployment.return_value = DeploymentResult(
            True, 
            url="https://testuser.github.io/testrepo",
            message="Deployed successfully",
            deployment_id="abc123"
        )
        mock_get_platform.return_value = mock_platform
        
        result = deploy_command(str(self.project_path))
        
        self.assertTrue(result)
        mock_platform.validate_credentials.assert_called_once()
        mock_platform.prepare_deployment.assert_called_once()
        mock_platform.execute_deployment.assert_called_once()
        mock_browser.assert_not_called()  # User declined browser open
    
    @patch('commands.deploy.get_platform')
    @patch('commands.deploy.questionary.confirm')
    @patch('commands.deploy.webbrowser.open')
    def test_deploy_success_with_browser_open(self, mock_browser, mock_confirm, mock_get_platform):
        """Test successful deployment with browser opening"""
        # Mock user confirmations
        mock_question = Mock()
        mock_question.ask.side_effect = [True, True]  # Deploy: Yes, Browser: Yes
        mock_confirm.return_value = mock_question
        
        # Mock successful platform
        mock_platform = Mock()
        mock_platform.validate_credentials.return_value = (True, "Valid")
        mock_platform.prepare_deployment.return_value = (True, "Ready")
        mock_platform.execute_deployment.return_value = DeploymentResult(
            True, url="https://testuser.github.io/testrepo"
        )
        mock_get_platform.return_value = mock_platform
        
        result = deploy_command(str(self.project_path))
        
        self.assertTrue(result)
        mock_browser.assert_called_once_with("https://testuser.github.io/testrepo")
    
    @patch('commands.deploy.questionary.confirm')
    def test_deploy_user_cancellation(self, mock_confirm):
        """Test deploy command when user cancels"""
        mock_confirm.return_value.ask.return_value = False  # User cancels deployment
        
        result = deploy_command(str(self.project_path))
        
        self.assertFalse(result)
    
    def test_show_deployment_summary_github_branch(self):
        """Test deployment summary display for GitHub branch method"""
        with patch('commands.deploy.questionary.confirm') as mock_confirm:
            mock_confirm.return_value.ask.return_value = True
            
            result = _show_deployment_summary(self.config_data)
            
            self.assertTrue(result)
            mock_confirm.assert_called_once()
    
    def test_show_deployment_summary_github_docs(self):
        """Test deployment summary display for GitHub docs method"""
        config_data = self.config_data.copy()
        config_data['github']['method'] = 'docs'
        
        with patch('commands.deploy.questionary.confirm') as mock_confirm:
            mock_confirm.return_value.ask.return_value = True
            
            result = _show_deployment_summary(config_data)
            
            self.assertTrue(result)
    
    @patch('commands.deploy.get_platform')
    def test_redeploy_no_config(self, mock_get_platform):
        """Test redeploy command without configuration"""
        # Remove config file
        config_path = self.project_path / 'deployx.yml'
        config_path.unlink()
        
        result = redeploy_command(str(self.project_path))
        
        self.assertFalse(result)
        mock_get_platform.assert_not_called()
    
    @patch('commands.deploy.get_platform')
    def test_redeploy_platform_failure(self, mock_get_platform):
        """Test redeploy command with platform initialization failure"""
        mock_get_platform.side_effect = Exception("Platform failed")
        
        result = redeploy_command(str(self.project_path))
        
        self.assertFalse(result)
    
    @patch('commands.deploy.get_platform')
    def test_redeploy_auth_failure(self, mock_get_platform):
        """Test redeploy command with authentication failure"""
        mock_platform = Mock()
        mock_platform.validate_credentials.return_value = (False, "Auth failed")
        mock_get_platform.return_value = mock_platform
        
        result = redeploy_command(str(self.project_path))
        
        self.assertFalse(result)
    
    @patch('commands.deploy.get_platform')
    def test_redeploy_preparation_failure(self, mock_get_platform):
        """Test redeploy command with preparation failure"""
        mock_platform = Mock()
        mock_platform.validate_credentials.return_value = (True, "Valid")
        mock_platform.prepare_deployment.return_value = (False, "Prep failed")
        mock_get_platform.return_value = mock_platform
        
        result = redeploy_command(str(self.project_path))
        
        self.assertFalse(result)
    
    @patch('commands.deploy.get_platform')
    def test_redeploy_success(self, mock_get_platform):
        """Test successful redeploy command"""
        mock_platform = Mock()
        mock_platform.validate_credentials.return_value = (True, "Valid")
        mock_platform.prepare_deployment.return_value = (True, "Ready")
        mock_platform.execute_deployment.return_value = DeploymentResult(
            True, url="https://testuser.github.io/testrepo"
        )
        mock_get_platform.return_value = mock_platform
        
        result = redeploy_command(str(self.project_path))
        
        self.assertTrue(result)
        mock_platform.validate_credentials.assert_called_once()
        mock_platform.prepare_deployment.assert_called_once()
        mock_platform.execute_deployment.assert_called_once()
    
    @patch('commands.deploy.get_platform')
    def test_redeploy_deployment_failure(self, mock_get_platform):
        """Test redeploy command with deployment failure"""
        mock_platform = Mock()
        mock_platform.validate_credentials.return_value = (True, "Valid")
        mock_platform.prepare_deployment.return_value = (True, "Ready")
        mock_platform.execute_deployment.return_value = DeploymentResult(
            False, message="Deploy failed"
        )
        mock_get_platform.return_value = mock_platform
        
        result = redeploy_command(str(self.project_path))
        
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()