#!/usr/bin/env python3

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from platforms.netlify.platform import NetlifyPlatform
from core.models import DeployXConfig


class TestNetlifyDeployment(unittest.TestCase):
    """Test Netlify platform deployment functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.project_path = Path(self.test_dir)
        
        # Create test config
        self.config = DeployXConfig(
            project={'name': 'test-app', 'type': 'react'},
            build={'command': 'npm run build', 'output': 'build'},
            platform='netlify',
            netlify={'site_id': 'test-site-id'}
        )
        
        # Create test files
        (self.project_path / 'build').mkdir()
        (self.project_path / 'build' / 'index.html').write_text('<html><body>Test</body></html>')
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    @patch('subprocess.run')
    def test_netlify_cli_deployment_success(self, mock_run):
        """Test successful Netlify CLI deployment."""
        mock_run.return_value = MagicMock(returncode=0, stdout='https://test-app.netlify.app')
        
        platform = NetlifyPlatform(self.config, str(self.project_path))
        
        success, message = platform.deploy()
        
        self.assertTrue(success)
        self.assertIn('deployed', message.lower())
    
    @patch('subprocess.run')
    def test_netlify_cli_deployment_failure(self, mock_run):
        """Test Netlify CLI deployment failure."""
        mock_run.return_value = MagicMock(returncode=1, stderr='Authentication failed')
        
        platform = NetlifyPlatform(self.config, str(self.project_path))
        
        success, message = platform.deploy()
        
        self.assertFalse(success)
        self.assertIn('failed', message.lower())
    
    @patch('platforms.netlify.api_integration.NetlifyAPIIntegration.deploy_site')
    def test_netlify_api_deployment_success(self, mock_deploy):
        """Test successful Netlify API deployment."""
        mock_deploy.return_value = (True, 'https://test-app.netlify.app')
        
        platform = NetlifyPlatform(self.config, str(self.project_path))
        platform.token = 'test_token'
        
        success, message = platform.deploy()
        
        self.assertTrue(success)
        self.assertIn('deployed', message.lower())
    
    @patch('platforms.netlify.api_integration.NetlifyAPIIntegration.deploy_site')
    def test_netlify_api_deployment_failure(self, mock_deploy):
        """Test Netlify API deployment failure."""
        mock_deploy.return_value = (False, 'API error: 401')
        
        platform = NetlifyPlatform(self.config, str(self.project_path))
        platform.token = 'invalid_token'
        
        success, message = platform.deploy()
        
        self.assertFalse(success)
        self.assertIn('error', message.lower())


if __name__ == '__main__':
    unittest.main()
