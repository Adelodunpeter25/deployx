"""
Global constants for DeployX.

Centralizes configuration values, timeouts, and magic numbers
used throughout the application.
"""

# Build Configuration
BUILD_TIMEOUT_SECONDS = 300  # 5 minutes max for build commands
MAX_BUILD_RETRIES = 3
BUILD_RETRY_DELAY = 2.0

# Network Configuration
NETWORK_TIMEOUT_SECONDS = 30
MAX_NETWORK_RETRIES = 3
RETRY_BACKOFF_BASE = 1.0

# UI Configuration
ANIMATION_FRAME_DELAY = 0.3
CELEBRATION_FRAMES = 5

# File Configuration
CONFIG_FILENAME = "deployx.yml"
TOKEN_FILE_PREFIX = ".deployx"
TOKEN_FILE_PERMISSIONS = 0o600  # Owner read/write only

# Deployment Configuration
MAX_DEPLOYMENT_ATTEMPTS = 3

# Platform Token URLs
GITHUB_TOKEN_URL = "https://github.com/settings/tokens"
VERCEL_TOKEN_URL = "https://vercel.com/account/tokens"
NETLIFY_TOKEN_URL = "https://app.netlify.com/user/applications#personal-access-tokens"
RAILWAY_TOKEN_URL = "https://railway.app/account/tokens"
RENDER_TOKEN_URL = "https://dashboard.render.com/account/api-keys"

# Supported Values
SUPPORTED_PLATFORMS = ["github", "vercel", "netlify", "railway", "render"]
SUPPORTED_PROJECT_TYPES = [
    "react", "vue", "static", "nextjs", "python", 
    "django", "flask", "fastapi", "nodejs", "angular", "vite"
]
