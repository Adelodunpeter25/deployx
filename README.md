# 🚀 DeployX - Deploy Anywhere with One Command

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


A modern CLI tool for deploying web projects to multiple platforms with zero configuration. Deploy your React, Next.js, or static sites to GitHub Pages, Vercel, and Netlify with a single command.

## ✨ Features

- 🎯 **Zero Configuration** - Auto-detects your project type and build settings
- 🌐 **Multiple Platforms** - GitHub Pages, Vercel, Netlify, Railway, Render support
- 🔧 **Framework Support** - React, Vue, Next.js, Angular, Django, Flask, FastAPI
- 📦 **Package Manager Detection** - npm, yarn, pnpm, bun, pip, poetry, pipenv, uv
- 🎨 **Beautiful CLI** - Rich terminal output with progress bars and spinners
- 🛡️ **Error Handling** - Clear error messages with actionable solutions
- 🔄 **CI/CD Ready** - Perfect for automated deployments
- 📋 **Deployment Logs** - View and stream deployment logs in real-time
- ⚙️ **Configuration Management** - Show, edit, and validate configurations
- 📊 **Deployment History** - Track past deployments with timestamps and status
- 🔍 **Dry Run Mode** - Preview deployments without executing them

## 🚀 Quick Start

### Installation

```bash
# Install with uv (recommended)
uv add deployx

# Or with pip
pip install deployx
```

### First Deployment

#### Option 1: Interactive Mode (Recommended for beginners)

1. **Navigate to your project directory**
   ```bash
   cd my-awesome-project
   ```

2. **Run interactive setup and deployment**
   ```bash
   deployx interactive
   ```
   
   This will automatically:
   - Analyze your project
   - Guide you through configuration
   - Deploy your project
   - Retry on failures with helpful options

#### Option 2: Step-by-step

1. **Navigate to your project directory**
   ```bash
   cd my-awesome-project
   ```

2. **Initialize deployment configuration**
   ```bash
   deployx init
   ```
   
   Expected output:
   ```
   🚀 DeployX - Deploy Anywhere with One Command
   Let's set up deployment for your project!

   🔍 Analyzing your project...
   📋 Project Analysis Results:
      Type: react
      Framework: react
      Build Command: npm run build
      Output Directory: build

   📡 Where do you want to deploy? GitHub Pages
   ⚙️ Configuring GitHub Pages...
   ✅ Configuration saved to deployx.yml
   ```

3. **Deploy your project**
   ```bash
   deployx deploy
   ```
   
   Expected output:
   ```
   🚀 Deploying to Github
   🔐 Validating credentials...
   ✅ GitHub credentials valid
   🔨 Preparing deployment...
   ✅ Build successful. 15 files ready for deployment
   🚀 Executing deployment...
   🎉 Deployment successful!
   🌐 Live URL: https://username.github.io/my-awesome-project
   ```

4. **Check deployment status**
   ```bash
   deployx status
   ```

5. **View deployment history and logs**
   ```bash
   deployx history              # See past deployments
   deployx logs                 # View deployment logs
   ```

That's it! Your project is now live. 🎉

### Additional Commands

**Preview before deploying:**
```bash
deployx deploy --dry-run        # See what would happen
```

**Manage configuration:**
```bash
deployx config show             # View current config
deployx config validate         # Check config is valid
```

## 📚 Command Reference

### `deployx interactive`

Run complete setup and deployment workflow in one command.

```bash
deployx interactive [OPTIONS]
```

**Options:**
- `--path, -p TEXT` - Project path (default: current directory)
- `--help` - Show help message

**Features:**
- Automatically runs init if no configuration exists
- Deploys your project with retry logic
- Handles failures with helpful recovery options
- Perfect for first-time users

**Examples:**
```bash
deployx interactive                 # Interactive mode in current directory
deployx interactive --path ./app    # Interactive mode in specific directory
```

### `deployx init`

Initialize deployment configuration for your project.

```bash
deployx init [OPTIONS]
```

**Options:**
- `--path, -p TEXT` - Project path (default: current directory)
- `--help` - Show help message

**Examples:**
```bash
deployx init                    # Initialize in current directory
deployx init --path ./my-app    # Initialize in specific directory
```

### `deployx deploy`

Deploy your project to the configured platform.

```bash
deployx deploy [OPTIONS]
```

**Options:**
- `--path, -p TEXT` - Project path (default: current directory)
- `--force, -f` - Skip confirmation prompts (for CI/CD)
- `--dry-run` - Show what would happen without deploying
- `--help` - Show help message

**Examples:**
```bash
deployx deploy                  # Interactive deployment
deployx deploy --force          # Skip confirmations (CI/CD)
deployx deploy --dry-run        # Preview deployment without executing
deployx deploy --path ./app     # Deploy specific directory
```

### `deployx status`

Check deployment status and information.

```bash
deployx status [OPTIONS]
```

**Options:**
- `--path, -p TEXT` - Project path (default: current directory)
- `--quick, -q` - Quick status check (returns exit code only)
- `--help` - Show help message

**Examples:**
```bash
deployx status                  # Full status information
deployx status --quick          # Quick check for CI/CD
```

**Exit codes (--quick mode):**
- `0` - Deployment is ready
- `1` - Deployment has issues
- `2` - Configuration not found

### `deployx logs`

View deployment logs from your platform.

```bash
deployx logs [OPTIONS]
```

**Options:**
- `--path, -p TEXT` - Project path (default: current directory)
- `--follow, -f` - Stream logs in real-time
- `--tail, -t NUMBER` - Number of lines to show from end
- `--help` - Show help message

**Examples:**
```bash
deployx logs                    # Show recent logs
deployx logs --follow           # Stream logs in real-time
deployx logs --tail 100         # Show last 100 lines
```

### `deployx config`

Configuration management commands.

```bash
deployx config show             # Show current configuration
deployx config edit             # Edit configuration file
deployx config validate         # Validate configuration
```

**Examples:**
```bash
deployx config show             # Display current config
deployx config edit             # Open config in $EDITOR
deployx config validate         # Check config without deploying
```

### `deployx history`

Show deployment history.

```bash
deployx history [OPTIONS]
```

**Options:**
- `--path, -p TEXT` - Project path (default: current directory)
- `--limit, -l NUMBER` - Number of deployments to show
- `--help` - Show help message

**Examples:**
```bash
deployx history                 # Show all deployment history
deployx history --limit 10      # Show last 10 deployments
```

### `deployx version`

Show version information and system details.

```bash
deployx version
```

### Global Options

Available for all commands:

- `--verbose, -v` - Enable verbose output for debugging
- `--version` - Show version information
- `--help` - Show help message

## 🛠️ Configuration

DeployX creates a `deployx.yml` file in your project root:

```yaml
# DeployX Configuration
project:
  name: "my-awesome-app"
  type: "react"

build:
  command: "npm run build"
  output: "build"

platform: "github"

github:
  repo: "username/repository"
  method: "branch"          # or "docs"
  branch: "gh-pages"
  token_env: "GITHUB_TOKEN"
```

### Platform Configuration

#### GitHub Pages

```yaml
github:
  repo: "username/repository"     # GitHub repository
  method: "branch"                # "branch" or "docs"
  branch: "gh-pages"             # Target branch (for branch method)
```

#### Vercel

```yaml
vercel: {}
```

#### Netlify

```yaml
netlify:
  site_id: "site-id"              # Optional: existing site ID
```

#### Railway

```yaml
railway:
  project_id: "project-id"        # Optional: existing project ID
```

#### Render

```yaml
render:
  name: "service-name"            # Service name
  type: "web_service"             # Service type
  environment: "node"             # Runtime environment
```

## 🔧 Environment Setup

### GitHub Pages Setup

1. **Create Personal Access Token**
   - Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
   - Click "Generate new token (classic)"
   - Select scopes: `repo`, `workflow`
   - Copy the token

2. **Token Storage**
   - DeployX will prompt for your token during `deployx init`
   - Token is saved securely to `.deployx_token` file
   - File is automatically added to `.gitignore`
   - **Never commit the token file to git!**

3. **Repository Setup**
   - Repository must exist on GitHub
   - You need write access to the repository
   - Enable GitHub Pages in repository settings (optional - DeployX can enable it)

### Vercel Setup

1. **Create Vercel Token**
   - Go to [Vercel Account Settings](https://vercel.com/account/tokens)
   - Create a new token
   - Copy the token

2. **Token Storage**
   - Token is saved to `.deployx_vercel_token` file
   - File is automatically added to `.gitignore`

### Netlify Setup

1. **Create Netlify Token**
   - Go to [Netlify User Settings](https://app.netlify.com/user/applications#personal-access-tokens)
   - Generate new token
   - Copy the token

2. **Token Storage**
   - Token is saved to `.deployx_netlify_token` file
   - File is automatically added to `.gitignore`

### Railway Setup

1. **Create Railway Token**
   - Go to [Railway Account Settings](https://railway.app/account/tokens)
   - Generate new token
   - Copy the token

2. **Token Storage**
   - Token is saved to `.deployx_railway_token` file
   - File is automatically added to `.gitignore`

### Render Setup

1. **Create Render API Key**
   - Go to [Render Dashboard > Account Settings > API Keys](https://dashboard.render.com/account/api-keys)
   - Create new API key
   - Copy the key (format: rnd_xxxxxxxxxxxxx)

2. **Token Storage**
   - Token is saved to `.deployx_render_token` file
   - File is automatically added to `.gitignore`

### Debug Mode

Use `--verbose` flag for detailed error information:

```bash
deployx deploy --verbose
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/deployx/deployx.git
   cd deployx
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

### Code Style Guidelines

- **Python**: Follow PEP 8
- **Type Hints**: Use type hints for all functions
- **Docstrings**: Document all public functions
- **Error Handling**: Use custom exception classes
- **Testing**: Write tests for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Click](https://click.palletsprojects.com/) for CLI framework
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- [PyGithub](https://pygithub.readthedocs.io/) for GitHub API integration

## 📞 Support

- 🐛 [Issue Tracker](https://github.com/deployx/deployx/issues)

---

Made with ❤️ by the DeployX team
