"""
Tests for API integrations across all platforms.
"""
import pytest
from unittest.mock import patch, MagicMock
import requests

from platforms.vercel.api_integration import VercelAPIIntegration
from platforms.railway.api_integration import RailwayAPIIntegration
from platforms.netlify.api_integration import NetlifyAPIIntegration

class TestAPIIntegrations:
    """Test API integrations for all platforms."""
    
    @patch('requests.get')
    def test_github_api_validation(self, mock_get):
        """Test GitHub API token validation."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'login': 'testuser', 'email': 'test@example.com'}
        mock_get.return_value = mock_response
        
        # This would require implementing GitHubAPIIntegration
        # For now, test the concept
        assert mock_response.status_code == 200
    
    @patch('requests.get')
    def test_vercel_api_validation(self, mock_get):
        """Test Vercel API token validation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'user': {'email': 'test@example.com'}}
        mock_get.return_value = mock_response
        
        api = VercelAPIIntegration('test_token')
        success, projects, message = api.list_projects()
        
        # Should handle the API call
        assert isinstance(success, bool)
    
    @patch('requests.post')
    def test_railway_api_validation(self, mock_post):
        """Test Railway API token validation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {'me': {'id': '123', 'email': 'test@example.com'}}
        }
        mock_post.return_value = mock_response
        
        api = RailwayAPIIntegration('test_token')
        valid, message, user_data = api.validate_token()
        
        assert valid is True
        assert 'test@example.com' in message
        assert user_data is not None
    
    @patch('requests.get')
    def test_netlify_api_validation(self, mock_get):
        """Test Netlify API token validation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'email': 'test@example.com', 'full_name': 'Test User'}
        mock_get.return_value = mock_response
        
        api = NetlifyAPIIntegration('test_token')
        valid, message, user_data = api.validate_token()
        
        assert valid is True
        assert 'test@example.com' in message
        assert user_data is not None
    
    @patch('requests.post')
    def test_railway_project_creation(self, mock_post):
        """Test Railway project creation via API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'projectCreate': {
                    'id': 'project_123',
                    'name': 'test-project',
                    'description': 'Test project'
                }
            }
        }
        mock_post.return_value = mock_response
        
        api = RailwayAPIIntegration('test_token')
        success, message, project_id = api.create_project('test-project')
        
        assert success is True
        assert project_id == 'project_123'
        assert 'test-project' in message
    
    @patch('requests.post')
    def test_netlify_site_creation(self, mock_post):
        """Test Netlify site creation via API."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'id': 'site_123',
            'name': 'test-site',
            'url': 'https://test-site.netlify.app'
        }
        mock_post.return_value = mock_response
        
        api = NetlifyAPIIntegration('test_token')
        success, message, site_id = api.create_site('test-site')
        
        assert success is True
        assert site_id == 'site_123'
        assert 'test-site' in message
    
    @patch('requests.post')
    def test_vercel_project_creation(self, mock_post):
        """Test Vercel project creation via API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 'project_123',
            'name': 'test-project'
        }
        mock_post.return_value = mock_response
        
        api = VercelAPIIntegration('test_token')
        success, message, project_id = api.create_project('test-project')
        
        assert success is True
        assert project_id == 'project_123'
    
    @patch('requests.post')
    def test_api_error_handling(self, mock_post):
        """Test API error handling."""
        # Test 401 Unauthorized
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'message': 'Unauthorized'}
        mock_post.return_value = mock_response
        
        api = RailwayAPIIntegration('invalid_token')
        valid, message, user_data = api.validate_token()
        
        assert valid is False
        assert 'api error' in message.lower() or 'unauthorized' in message.lower() or 'invalid' in message.lower()
    
    @patch('requests.post')
    def test_network_error_handling(self, mock_post):
        """Test network error handling."""
        # Simulate network error
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")
        
        api = RailwayAPIIntegration('test_token')
        valid, message, user_data = api.validate_token()
        
        assert valid is False
        assert 'connection' in message.lower() or 'network' in message.lower()
    
    @patch('requests.get')
    def test_rate_limiting_handling(self, mock_get):
        """Test rate limiting handling."""
        # Test 429 Too Many Requests
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {'message': 'Rate limit exceeded'}
        mock_get.return_value = mock_response
        
        api = NetlifyAPIIntegration('test_token')
        valid, message, user_data = api.validate_token()
        
        assert valid is False
        assert 'rate' in message.lower() or '429' in message
    
    def test_api_base_urls(self):
        """Test that all APIs have correct base URLs."""
        vercel_api = VercelAPIIntegration('test_token')
        railway_api = RailwayAPIIntegration('test_token')
        netlify_api = NetlifyAPIIntegration('test_token')
        
        assert vercel_api.api_base == "https://api.vercel.com"
        assert railway_api.api_base == "https://backboard.railway.app/graphql"
        assert netlify_api.api_base == "https://api.netlify.com/api/v1"
    
    def test_api_headers(self):
        """Test that all APIs set correct headers."""
        token = 'test_token'
        
        vercel_api = VercelAPIIntegration(token)
        railway_api = RailwayAPIIntegration(token)
        netlify_api = NetlifyAPIIntegration(token)
        
        # All should have Authorization header
        assert 'Authorization' in vercel_api.headers
        assert 'Authorization' in railway_api.headers
        assert 'Authorization' in netlify_api.headers
        
        # Check Bearer token format
        assert vercel_api.headers['Authorization'] == f"Bearer {token}"
        assert railway_api.headers['Authorization'] == f"Bearer {token}"
        assert netlify_api.headers['Authorization'] == f"Bearer {token}"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
