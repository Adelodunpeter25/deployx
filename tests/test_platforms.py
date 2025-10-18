"""
Tests for platform implementations
"""

import pytest
import os
from unittest.mock import patch
from platforms.factory import PlatformFactory
from platforms.github import GitHubPlatform
from platforms.vercel import VercelPlatform
from platforms.netlify import NetlifyPlatform
from platforms.railway import RailwayPlatform

def test_platform_registration():
    """Test that all platforms are properly registered"""
    available_platforms = PlatformFactory.get_available_platforms()
    
    expected_platforms = ["github", "vercel", "netlify", "railway"]
    
    for platform in expected_platforms:
        assert platform in available_platforms, f"Platform {platform} not registered"

@patch.dict(os.environ, {
    'GITHUB_TOKEN': 'fake_github_token',
    'VERCEL_TOKEN': 'fake_vercel_token', 
    'NETLIFY_TOKEN': 'fake_netlify_token',
    'RAILWAY_TOKEN': 'fake_railway_token'
})
def test_platform_creation():
    """Test that platforms can be created"""
    config = {
        "project": {"name": "test-project", "type": "react"},
        "build": {"command": "npm run build", "output": "build"},
        "platform": "github"
    }
    
    # Test GitHub platform creation
    github_config = {**config, "github": {"repo": "test/repo", "method": "branch", "branch": "gh-pages"}}
    github_platform = PlatformFactory.create_platform("github", github_config)
    assert isinstance(github_platform, GitHubPlatform)
    
    # Test Vercel platform creation
    vercel_config = {**config, "vercel": {"token_env": "VERCEL_TOKEN"}}
    vercel_platform = PlatformFactory.create_platform("vercel", vercel_config)
    assert isinstance(vercel_platform, VercelPlatform)
    
    # Test Netlify platform creation
    netlify_config = {**config, "netlify": {"token_env": "NETLIFY_TOKEN"}}
    netlify_platform = PlatformFactory.create_platform("netlify", netlify_config)
    assert isinstance(netlify_platform, NetlifyPlatform)
    
    # Test Railway platform creation
    railway_config = {**config, "railway": {"token_env": "RAILWAY_TOKEN"}}
    railway_platform = PlatformFactory.create_platform("railway", railway_config)
    assert isinstance(railway_platform, RailwayPlatform)

def test_invalid_platform():
    """Test that invalid platform raises error"""
    config = {"project": {"name": "test"}}
    
    with pytest.raises(ValueError, match="Unknown platform"):
        PlatformFactory.create_platform("invalid", config)