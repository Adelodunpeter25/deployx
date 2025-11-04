"""
Tests for Phase 2 Smart Token Wizard features.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from commands.auth import auth_status_command, auth_setup_command, auth_clear_command
from platforms.github.auto_creation import GitHubAutoCreation
from platforms.vercel.auto_creation import VercelAutoCreation
from platforms.railway.auto_creation import RailwayAutoCreation
from platforms.netlify.auto_creation import NetlifyAutoCreation

class TestPhase2Features:
    """Test Phase 2 Smart Token Wizard and auto-creation features."""
    
    def setup_method(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
    
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)
    
    def test_auth_status_command(self):
        """Test auth status command."""
        result = auth_status_command()
        assert result is True
    
    @patch('webbrowser.open')
    @patch('builtins.input', side_effect=['y', 'test_token'])
    @patch('commands.auth._test_platform_token', return_value=True)
    def test_auth_setup_github(self, mock_test, mock_input, mock_browser):
        """Test GitHub auth setup."""
        result = auth_setup_command('github')
        
        assert result is True
        mock_browser.assert_called_once()
        
        # Check token file was created
        token_file = Path('.deployx_github_token')
        assert token_file.exists()
        assert token_file.read_text().strip() == 'test_token'
    
    @patch('webbrowser.open')
    @patch('builtins.input', side_effect=['y', 'test_token'])
    @patch('commands.auth._test_platform_token', return_value=True)
    def test_auth_setup_vercel(self, mock_test, mock_input, mock_browser):
        """Test Vercel auth setup."""
        result = auth_setup_command('vercel')
        
        assert result is True
        mock_browser.assert_called_once()
        
        # Check token file was created
        token_file = Path('.deployx_vercel_token')
        assert token_file.exists()
    
    def test_auth_clear_command(self):
        """Test auth clear command."""
        # Create a token file
        token_file = Path('.deployx_github_token')
        token_file.write_text('test_token')
        
        # Clear it
        result = auth_clear_command('github')
        
        assert result is True
        assert not token_file.exists()
    
    def test_auth_setup_invalid_platform(self):
        """Test auth setup with invalid platform."""
        result = auth_setup_command('invalid_platform')
        assert result is False
    
    @patch('builtins.input', side_effect=['n'])
    def test_auth_setup_cancelled(self, mock_input):
        """Test auth setup when user cancels."""
        # Create existing token
        token_file = Path('.deployx_github_token')
        token_file.write_text('existing_token')
        
        result = auth_setup_command('github')
        
        # Should return True (existing config kept)
        assert result is True
        assert token_file.exists()
    
    @patch('subprocess.run')
    def test_github_auto_creation_detection(self, mock_run):
        """Test GitHub auto-creation detection."""
        auto_creation = GitHubAutoCreation(None)
        
        # Mock git status to return failure (no git repo)
        mock_run.return_value = MagicMock(returncode=1)
        should_create, reason = auto_creation.should_create_repository(self.test_dir)
        assert should_create
        assert 'no git repository' in reason.lower()
        
        # Mock git status success but no remote
        mock_run.side_effect = [
            MagicMock(returncode=0),  # git status succeeds
            MagicMock(returncode=0, stdout="")  # git remote -v returns empty
        ]
        should_create, reason = auto_creation.should_create_repository(self.test_dir)
        assert should_create
        assert 'no remote origin' in reason.lower()
    
    def test_vercel_auto_creation_detection(self):
        """Test Vercel auto-creation detection."""
        auto_creation = VercelAutoCreation(None)
        
        # Should want to create in empty directory
        should_create, reason = auto_creation.should_create_project(self.test_dir)
        assert should_create
        assert 'no vercel project' in reason.lower()
        
        # Create .vercel directory
        os.makedirs('.vercel')
        should_create, reason = auto_creation.should_create_project(self.test_dir)
        assert not should_create
        assert 'already configured' in reason.lower()
    
    def test_railway_auto_creation_detection(self):
        """Test Railway auto-creation detection."""
        auto_creation = RailwayAutoCreation(None)
        
        # Should want to create in empty directory
        should_create, reason = auto_creation.should_create_project(self.test_dir)
        assert should_create
        assert 'no railway project' in reason.lower()
        
        # Create .railway directory
        os.makedirs('.railway')
        should_create, reason = auto_creation.should_create_project(self.test_dir)
        assert not should_create
        assert 'already configured' in reason.lower()
    
    def test_netlify_auto_creation_detection(self):
        """Test Netlify auto-creation detection."""
        auto_creation = NetlifyAutoCreation(None)
        
        # Should want to create in empty directory
        should_create, reason = auto_creation.should_create_site(self.test_dir)
        assert should_create
        assert 'no netlify site' in reason.lower()
        
        # Create .netlify directory
        os.makedirs('.netlify')
        should_create, reason = auto_creation.should_create_site(self.test_dir)
        assert not should_create
        assert 'already configured' in reason.lower()
    
    @patch('builtins.input', return_value='my-custom-name')
    def test_project_name_prompts(self, mock_input):
        """Test project name prompting."""
        auto_creation = GitHubAutoCreation(None)
        
        # Test name generation
        suggested = auto_creation._generate_suggested_name('My Test Project')
        assert suggested == 'my-test-project'
        
        # Test custom name input
        custom_name = auto_creation._prompt_for_repo_name('suggested-name')
        assert custom_name == 'my-custom-name'
    
    @patch('subprocess.run')
    def test_cli_integrations(self, mock_run):
        """Test CLI integrations."""
        from platforms.github.cli_integration import GitHubCLIIntegration
        from platforms.vercel.cli_integration import VercelCLIIntegration
        from platforms.railway.cli_integration import RailwayCLIIntegration
        from platforms.netlify.cli_integration import NetlifyCLIIntegration
        
        # Mock CLI not available
        mock_run.return_value = MagicMock(returncode=1)
        
        github_cli = GitHubCLIIntegration()
        vercel_cli = VercelCLIIntegration()
        railway_cli = RailwayCLIIntegration()
        netlify_cli = NetlifyCLIIntegration()
        
        assert not github_cli.is_cli_available()
        assert not vercel_cli.is_cli_available()
        assert not railway_cli.is_cli_available()
        assert not netlify_cli.is_cli_available()
        
        # Mock CLI available
        mock_run.return_value = MagicMock(returncode=0, stdout="Logged in")
        
        assert github_cli.is_cli_available()
        assert vercel_cli.is_cli_available()
        assert railway_cli.is_cli_available()
        assert netlify_cli.is_cli_available()
    
    @patch('requests.get')
    def test_token_validation(self, mock_get):
        """Test token validation for all platforms."""
        from commands.auth import _test_platform_token
        
        # Mock successful API responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Test all platforms
        platforms = ['netlify', 'render']
        for platform in platforms:
            result = _test_platform_token(platform, 'test_token')
            assert result is True
        
        # Test failed validation
        mock_response.status_code = 401
        result = _test_platform_token('netlify', 'invalid_token')
        assert result is False
    
    def test_token_file_management(self):
        """Test token file creation and management."""
        platforms = ['github', 'vercel', 'railway', 'netlify', 'render']
        
        for platform in platforms:
            token_file = Path(f'.deployx_{platform}_token')
            
            # Create token file
            token_file.write_text('test_token')
            assert token_file.exists()
            
            # Clear token file
            result = auth_clear_command(platform)
            assert result is True
            assert not token_file.exists()
    
    @patch('builtins.input', side_effect=KeyboardInterrupt())
    def test_setup_cancellation(self, mock_input):
        """Test setup cancellation handling."""
        result = auth_setup_command('github')
        assert result is False
    
    def test_suggested_name_generation(self):
        """Test suggested name generation for all platforms."""
        test_cases = [
            ('My Test Project', 'my-test-project'),
            ('test_app_name', 'test-app-name'),
            ('TestApp123', 'testapp123'),
            ('app with spaces', 'app-with-spaces'),
            ('', 'my-project'),  # Fallback for empty names
        ]
        
        auto_creation = GitHubAutoCreation(None)
        
        for input_name, expected in test_cases:
            result = auto_creation._generate_suggested_name(input_name)
            assert result == expected
    
    def test_hybrid_authentication_priority(self):
        """Test hybrid authentication priority order."""
        from platforms.github.platform import GitHubPlatform
        
        # Test priority: CLI > Token file > Environment
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'env_token'}):
            # Create token file
            token_file = Path('.deployx_github_token')
            token_file.write_text('file_token')
            
            platform = GitHubPlatform({'github': {}})
            
            # Should prefer file over environment
            token = platform._get_token()
            assert token == 'file_token'
            
            # Remove file, should use environment
            token_file.unlink()
            token = platform._get_token()
            assert token == 'env_token'

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
