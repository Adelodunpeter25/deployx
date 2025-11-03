# 🚀 DeployX

One CLI for all your deployments  

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

DeployX eliminates the complexity of platform-specific deployment commands. One CLI for all your deployments - just run `deployx deploy` and watch your project go live.

No more memorizing different CLI tools, configuration formats, or deployment workflows.

## ✨ Features

- 🎯 **Zero Configuration** - Auto-detects your project type and build settings
- 🌐 **Multiple Platforms** - GitHub Pages, Vercel, Netlify, Railway, Render support
- 🔧 **Framework Support** - React, Vue, Next.js, Angular, Django, Flask, FastAPI
- 📦 **Package Manager Detection** - npm, yarn, pnpm, bun, pip, poetry, pipenv, uv
- 🌍 **Environment Variables** - Auto-detect .env files and configure across platforms
- ⚡ **Auto-Service Creation** - Automatically creates services on Render and other platforms
- 🎨 **Beautiful CLI** - Rich terminal output with progress bars and spinners
- 🔄 **CI/CD Ready** - Perfect for automated deployments
- 📋 **Deployment Logs** - View and stream deployment logs in real-time
- ⚙️ **Configuration Management** - Show, edit, and validate configurations
- 📊 **Deployment History** - Track past deployments with timestamps and status
- 🔙 **Rollback Support** - Revert to previous deployments with one command
- 🔍 **Dry Run Mode** - Preview deployments without executing them

## 🚀 Quick Start

### Installation

```bash
# Install with pip
pip install deployx

# Or with uv (recommended)
uv add deployx
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
- Configure build settings automatically  
- Set up the deployment platform
- Handle environment variables from .env files
- Deploy your project and provide a live URL

🎉 **Your project is now live!**

### Advanced Usage

**Interactive setup for full control:**
```bash
deployx interactive
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

## ⚡ Auto-Service Creation

For platforms like Render, DeployX automatically creates services when needed:

- **Smart Detection**: Determines if you need a static site or web service
- **Auto-Configuration**: Sets up build commands and publish paths
- **Service Management**: Creates and configures services via platform APIs
- **Zero Manual Setup**: No need to create services manually in dashboards

## 📚 Commands

```bash
# Quick deployment
deployx deploy                  # Auto-detect and deploy
deployx deploy --dry-run        # Preview without deploying
deployx deploy --force          # Skip confirmations

# Setup and configuration
deployx init                    # Initialize configuration
deployx interactive             # Guided setup and deployment

# Monitoring and management
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

DeployX will prompt for tokens during setup. Get them from:

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
