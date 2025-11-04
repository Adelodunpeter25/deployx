# 🚀 DeployX

One CLI for all your deployments  

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

DeployX eliminates the complexity of platform-specific deployment commands. One CLI for all your deployments - just run `deployx deploy` and watch your project go live.

No more memorizing different CLI tools, configuration formats, or deployment workflows.

## ✨ Features

- **Zero Configuration** - Auto-detects your project type and build settings
- **Multiple Platforms** - GitHub Pages, Vercel, Netlify, Railway, Render support
- **Framework Support** - React, Vue, Next.js, Angular, Django, Flask, FastAPI
-**Package Manager Detection** - npm, yarn, pnpm, bun, pip, poetry, pipenv, uv
- **Environment Variables** - Auto-detect .env files and configure across platforms
-  **Auto-Service Creation** - Automatically creates services on Render and other platforms
- **Beautiful CLI** - Rich terminal output with progress bars and spinners
- **CI/CD Ready** - Perfect for automated deployments
-**Deployment Logs** - View and stream deployment logs in real-time
- **Configuration Management** - Show, edit, and validate configurations
- **Deployment History** - Track past deployments with timestamps and status
- **Rollback Support** - Revert to previous deployments with one command
- **Dry Run Mode** - Preview deployments without executing them

## 🚀 Quick Start

### Installation

```bash
# Quick install with curl (recommended)
curl -fsSL https://raw.githubusercontent.com/Adelodunpeter25/deployx/main/install.sh | bash

# Or install with pip
pip install deployx

# Or with uv
uv add deployx
```

**Uninstall:**
```bash
# Using uninstall script
curl -fsSL https://raw.githubusercontent.com/Adelodunpeter25/deployx/main/uninstall.sh | bash

# Or with pip
pip uninstall deployx
```

### First Deployment (Beginner-Friendly)

1. **Navigate to your project**
   ```bash
   cd my-project
   ```

2. **Deploy in one command**
   ```bash
   deployx deploy
   ```

That's it! DeployX will:
- Auto-detect your project type and framework
- Use existing CLI authentication (GitHub CLI, Vercel CLI, etc.) if available
- Guide you through token setup if needed with auto-opening browser pages
- Auto-create repositories/projects/services as needed
- Configure build settings automatically  
- Handle environment variables from .env files
- Deploy your project and provide a live URL

🎉 **Your project is now live!**

### Advanced Usage

**Interactive setup for full control:**
```bash
deployx interactive
```

**Authentication management:**
```bash
deployx auth status          # Check authentication status for all platforms
deployx auth setup github    # Guided GitHub token setup
deployx auth clear railway   # Clear stored Railway token
```

**Step-by-step configuration:**
```bash
deployx init      # Initialize configuration
deployx deploy    # Deploy your project
deployx status    # Check deployment status
```

**Environment variable management:**
```bash
deployx deploy    # Auto-detects .env files and prompts for configuration
```

**Preview before deploying:**
```bash
deployx deploy --dry-run
```

## 🔐 Authentication

DeployX uses a **hybrid authentication system** that prioritizes convenience:

### **Automatic CLI Detection**
If you have platform CLIs installed, DeployX uses them automatically:
- **GitHub CLI** (`gh`) - Uses existing authentication
- **Vercel CLI** - Uses existing authentication  

### **Smart Token Wizard**
For platforms without CLI or when CLI isn't authenticated:
```bash
deployx auth setup github
# 🎯 Setting up GitHub authentication
# 📝 Create a token with 'repo' and 'workflow' scopes
# 🔗 Open GitHub token page? (Y/n): y
# ✅ Opened GitHub token page in browser
# 📋 Paste your GitHub token: [secure input]
# ✅ GitHub token saved
# 🔐 Testing GitHub connection...
# ✅ GitHub configured successfully!
```

### **Authentication Status**
```bash
deployx auth status
# ✅ GitHub: Connected via CLI (username)
# ✅ Vercel: Connected via CLI (username)
# ✅ Railway: Connected via token file
# ❌ Netlify: Not configured
#    Run: deployx auth setup netlify
```

## 🌍 Environment Variables

DeployX automatically detects `.env` files and helps configure environment variables across platforms:

- **Auto-Detection**: Finds `.env`, `.env.local`, `.env.production` files
- **Multiple Input Methods**: Auto-configure, paste manually, or add interactively
- **Platform Integration**: Sets variables as GitHub secrets, Render service vars, etc.
- **User Control**: Choose which variables to configure and preview before setting

```bash
# During deployment, DeployX will prompt:
🔍 Found .env file with 5 variables
📋 Variables: NODE_ENV, API_URL, DATABASE_URL, JWT_SECRET, etc.
❓ Configure environment variables for GitHub? (y/n)
```
## 📚 Commands

### **Core Commands**
```bash
# Quick deployment
deployx deploy                  # Auto-detect and deploy
deployx deploy --dry-run        # Preview without deploying
deployx deploy --force          # Skip confirmations

# Setup and configuration
deployx init                    # Initialize configuration
deployx interactive             # Guided setup and deployment
```

### **Authentication Commands**
```bash
deployx auth status             # Show authentication status for all platforms
deployx auth setup <platform>   # Guided token setup (github, vercel, railway, etc.)
deployx auth clear <platform>   # Clear stored authentication
```

### **Monitoring and Management**
```bash
deployx status                  # Check deployment status
deployx logs --follow           # Stream deployment logs
deployx history --limit 10      # View deployment history

# Configuration management
deployx config show             # View current config
deployx config edit             # Edit configuration
deployx config validate         # Validate configuration

# Rollback and recovery
deployx rollback                # Interactive rollback selection
deployx rollback --target 2     # Rollback to specific deployment
```

Use `deployx [command] --help` for detailed options.

## 🛠️ Configuration

DeployX creates a `deployx.yml` file in your project root:

```yaml
project:
  name: "my-app"
  type: "react"

build:
  command: "npm run build"
  output: "build"

platform: "github"

github:
  repo: "username/repository"
  method: "branch"
  branch: "gh-pages"

# Environment variables are managed automatically
# but can be configured per platform if needed
```

## 🔧 Platform Setup

### **Automatic Setup (Recommended)**
If you have platform CLIs installed, DeployX works immediately:
```bash
# Install platform CLIs for zero-config experience
gh auth login          # GitHub CLI
vercel login           # Vercel CLI  
railway login          # Railway CLI
```

### **Manual Token Setup**
Use the guided wizard for platforms without CLI:
```bash
deployx auth setup <platform>
```

Or get tokens manually from:
- **GitHub**: [Settings > Tokens](https://github.com/settings/tokens) (needs `repo`, `workflow`)
- **Vercel**: [Account Settings](https://vercel.com/account/tokens)
- **Netlify**: [User Settings](https://app.netlify.com/user/applications#personal-access-tokens)
- **Railway**: [Account Settings](https://railway.app/account/tokens)
- **Render**: [API Keys](https://dashboard.render.com/account/api-keys)

Tokens are saved securely and added to `.gitignore` automatically.

## 🤝 Contributing

Contributions welcome! 

```bash
git clone https://github.com/Adelodunpeter25/deployx.git
cd deployx
uv sync
```

Follow PEP 8, add type hints, add docstrings and write tests for new features.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Made with ❤️ by Adelodun Peter
