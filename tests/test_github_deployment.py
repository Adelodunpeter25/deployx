#!/usr/bin/env python3

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from platforms.github.platform import GitHubPlatform
from core.models import DeployXConfig


class TestGitHubDeployment(unittest.TestCase):
    """Test GitHub platform deployment functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.project_path = Path(self.test_dir)
        
        # Create test config
        self.config = DeployXConfig(
            project={'name': 'test-app', 'type': 'react'},
            build={'command': 'npm run build', 'output': 'build'},
            platform='github',
            github={'repo': 'testuser/testrepo', 'method': 'branch', 'branch': 'gh-pages'}
        )
        
        # Create test files
        (self.project_path / 'build').mkdir()
        (self.project_path / 'build' / 'index.html').write_text('<html><body>Test</body></html>')
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    @patch('platforms.github.platform.Github')
    def test_github_deployment_success(self, mock_github):
        """Test successful GitHub deployment."""
        # Mock GitHub API
        mock_repo = MagicMock()
        mock_github.return_value.get_repo.return_value = mock_repo
        
        platform = GitHubPlatform(self.config, str(self.project_path))
        platform.token = 'test_token'
        
        success, message = platform.deploy()
        
        self.assertTrue(success)
        self.assertIn('deployed', message.lower())
    
    @patch('platforms.github.platform.Github')
    def test_github_deployment_auth_failure(self, mock_github):
        """Test GitHub deployment with authentication failure."""
        mock_github.side_effect = Exception("Bad credentials")
        
        platform = GitHubPlatform(self.config, str(self.project_path))
        platform.token = 'invalid_token'
        
        success, message = platform.deploy()
        
        self.assertFalse(success)
        self.assertIn('credential', message.lower())
    
    def test_github_deployment_no_token(self):
        """Test GitHub deployment without token."""
        platform = GitHubPlatform(self.config, str(self.project_path))
        
        success, message = platform.deploy()
        
        self.assertFalse(success)
        self.assertIn('token', message.lower())
    
    def test_github_deployment_no_build_output(self):
        """Test GitHub deployment with missing build output."""
        # Remove build directory
        shutil.rmtree(self.project_path / 'build')
        
        platform = GitHubPlatform(self.config, str(self.project_path))
        platform.token = 'test_token'
        
        success, message = platform.deploy()
        
        self.assertFalse(success)
        self.assertIn('not found', message.lower())


if __name__ == '__main__':
    unittest.main()
