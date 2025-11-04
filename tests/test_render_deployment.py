#!/usr/bin/env python3

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from platforms.render.platform import RenderPlatform
from core.models import DeploymentConfig


class TestRenderDeployment(unittest.TestCase):
    """Test Render platform deployment functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.project_path = Path(self.test_dir)
        
        # Create test config
        self.config = DeploymentConfig(
            project={'name': 'test-app', 'type': 'static'},
            build={'command': 'npm run build', 'output': 'build'},
            platform='render',
            render={'service_id': 'test-service-id'}
        )
        
        # Create test files
        (self.project_path / 'build').mkdir()
        (self.project_path / 'build' / 'index.html').write_text('<html><body>Test</body></html>')
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    @patch('platforms.render.api_integration.RenderAPIIntegration.create_service')
    def test_render_service_creation_success(self, mock_create):
        """Test successful Render service creation."""
        mock_create.return_value = (True, 'test-service-id')
        
        platform = RenderPlatform(self.config, str(self.project_path))
        platform.token = 'test_token'
        
        success, service_id = platform.create_service()
        
        self.assertTrue(success)
        self.assertEqual(service_id, 'test-service-id')
    
    @patch('platforms.render.api_integration.RenderAPIIntegration.create_service')
    def test_render_service_creation_failure(self, mock_create):
        """Test Render service creation failure."""
        mock_create.return_value = (False, 'API error: 401')
        
        platform = RenderPlatform(self.config, str(self.project_path))
        platform.token = 'invalid_token'
        
        success, message = platform.create_service()
        
        self.assertFalse(success)
        self.assertIn('error', message.lower())
    
    @patch('platforms.render.api_integration.RenderAPIIntegration.deploy_service')
    def test_render_deployment_success(self, mock_deploy):
        """Test successful Render deployment."""
        mock_deploy.return_value = (True, 'https://test-app.onrender.com')
        
        platform = RenderPlatform(self.config, str(self.project_path))
        platform.token = 'test_token'
        
        success, message = platform.deploy()
        
        self.assertTrue(success)
        self.assertIn('deployed', message.lower())
    
    @patch('platforms.render.api_integration.RenderAPIIntegration.deploy_service')
    def test_render_deployment_failure(self, mock_deploy):
        """Test Render deployment failure."""
        mock_deploy.return_value = (False, 'API error: 401')
        
        platform = RenderPlatform(self.config, str(self.project_path))
        platform.token = 'invalid_token'
        
        success, message = platform.deploy()
        
        self.assertFalse(success)
        self.assertIn('error', message.lower())
    
    def test_render_deployment_no_token(self):
        """Test Render deployment without token."""
        platform = RenderPlatform(self.config, str(self.project_path))
        
        success, message = platform.deploy()
        
        self.assertFalse(success)
        self.assertIn('token', message.lower())


if __name__ == '__main__':
    unittest.main()
