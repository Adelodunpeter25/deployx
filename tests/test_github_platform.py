import unittest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from platforms.github import GitHubPlatform
from platforms.factory import PlatformFactory

class TestGitHubPlatform(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.config = {
            'repo': 'testuser/testrepo',
            'method': 'branch',
            'branch': 'gh-pages',
            'token_env': 'GITHUB_TOKEN'
        }
        
        # Set fake token
        os.environ['GITHUB_TOKEN'] = 'fake_github_token_12345'
        
        # Create temporary project directory
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir)
        
        # Create fake build output
        self.output_dir = self.project_path / 'build'
        self.output_dir.mkdir()
        (self.output_dir / 'index.html').write_text('<html><body>Test</body></html>')
        (self.output_dir / 'style.css').write_text('body { color: red; }')
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
        if 'GITHUB_TOKEN' in os.environ:
            del os.environ['GITHUB_TOKEN']
    
    def test_platform_creation(self):
        """Test GitHub platform creation"""
        platform = GitHubPlatform(self.config)
        
        self.assertEqual(platform.repo_name, 'testuser/testrepo')
        self.assertEqual(platform.method, 'branch')
        self.assertEqual(platform.branch, 'gh-pages')
        self.assertEqual(platform.token, 'fake_github_token_12345')
    
    def test_platform_factory_registration(self):
        """Test platform is registered with factory"""
        available_platforms = PlatformFactory.get_available_platforms()
        self.assertIn('github', available_platforms)
        
        platform = PlatformFactory.create_platform('github', self.config)
        self.assertIsInstance(platform, GitHubPlatform)
    
    def test_validate_credentials_no_token(self):
        """Test credential validation without token"""
        del os.environ['GITHUB_TOKEN']
        platform = GitHubPlatform(self.config)
        
        valid, message = platform.validate_credentials()
        
        self.assertFalse(valid)
        self.assertIn('token not found', message)
    
    def test_validate_credentials_no_repo(self):
        """Test credential validation without repo"""
        config = self.config.copy()
        config['repo'] = None
        platform = GitHubPlatform(config)
        
        valid, message = platform.validate_credentials()
        
        self.assertFalse(valid)
        self.assertIn('Repository name not configured', message)
    
    @patch('platforms.github.Github')
    def test_validate_credentials_success(self, mock_github):
        """Test successful credential validation"""
        # Mock GitHub API
        mock_client = Mock()
        mock_repo = Mock()
        mock_github.return_value = mock_client
        mock_client.get_repo.return_value = mock_repo
        mock_repo.get_contents.return_value = Mock()
        
        platform = GitHubPlatform(self.config)
        valid, message = platform.validate_credentials()
        
        self.assertTrue(valid)
        self.assertIn('valid', message)
        mock_github.assert_called_with('fake_github_token_12345')
    
    @patch('platforms.github.Github')
    def test_validate_credentials_failure(self, mock_github):
        """Test credential validation failure"""
        # Mock GitHub API to raise exception
        mock_github.side_effect = Exception("Invalid token")
        
        platform = GitHubPlatform(self.config)
        valid, message = platform.validate_credentials()
        
        self.assertFalse(valid)
        self.assertIn('validation failed', message)
    
    def test_prepare_deployment_no_output_dir(self):
        """Test preparation when output directory doesn't exist"""
        platform = GitHubPlatform(self.config)
        
        success, message = platform.prepare_deployment(str(self.project_path), None, 'nonexistent')
        
        self.assertFalse(success)
        self.assertIn('not found', message)
    
    def test_prepare_deployment_empty_output_dir(self):
        """Test preparation with empty output directory"""
        empty_dir = self.project_path / 'empty'
        empty_dir.mkdir()
        
        platform = GitHubPlatform(self.config)
        success, message = platform.prepare_deployment(str(self.project_path), None, 'empty')
        
        self.assertFalse(success)
        self.assertIn('No files found', message)
    
    def test_prepare_deployment_success(self):
        """Test successful deployment preparation"""
        platform = GitHubPlatform(self.config)
        
        success, message = platform.prepare_deployment(str(self.project_path), None, 'build')
        
        self.assertTrue(success)
        self.assertIn('2 files ready', message)
    
    @patch('platforms.github.subprocess.run')
    def test_prepare_deployment_with_build_command(self, mock_run):
        """Test preparation with build command"""
        mock_run.return_value = Mock(returncode=0)
        
        platform = GitHubPlatform(self.config)
        success, message = platform.prepare_deployment(str(self.project_path), 'npm run build', 'build')
        
        self.assertTrue(success)
        mock_run.assert_called_once()
    
    @patch('platforms.github.subprocess.run')
    def test_prepare_deployment_build_failure(self, mock_run):
        """Test preparation with failed build command"""
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(1, 'npm', stderr='Build failed')
        
        platform = GitHubPlatform(self.config)
        success, message = platform.prepare_deployment(str(self.project_path), 'npm run build', 'build')
        
        self.assertFalse(success)
        self.assertIn('Build failed', message)
    
    def test_get_url(self):
        """Test URL generation"""
        platform = GitHubPlatform(self.config)
        
        url = platform.get_url()
        
        self.assertEqual(url, 'https://testuser.github.io/testrepo')
    
    def test_get_url_no_repo(self):
        """Test URL generation without repo"""
        config = self.config.copy()
        config['repo'] = None
        platform = GitHubPlatform(config)
        
        url = platform.get_url()
        
        self.assertIsNone(url)
    
    @patch('platforms.github.GitHubPlatform.validate_credentials')
    def test_get_status_unknown(self, mock_validate):
        """Test status check when pages not configured"""
        mock_validate.return_value = (True, "Valid")
        
        platform = GitHubPlatform(self.config)
        platform.repo_obj = Mock()
        platform.repo_obj.get_pages_build.side_effect = Exception("Not found")
        
        status = platform.get_status()
        
        self.assertEqual(status.status, 'unknown')
        self.assertIn('not configured', status.message)

if __name__ == '__main__':
    unittest.main()