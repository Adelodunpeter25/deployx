# 🚀 DeployX - Deploy Anywhere with One Command

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


A modern CLI tool for deploying web projects to multiple platforms with zero configuration. Deploy your React, Next.js, or static sites to GitHub Pages, Vercel, and Netlify with a single command.

## ✨ Features

- 🎯 **Zero Configuration** - Auto-detects your project type and build settings
- 🌐 **Multiple Platforms** - GitHub Pages, Vercel, Netlify support
- 🔧 **Framework Support** - React, Vue, Next.js, Angular, Django, Flask, FastAPI
- 📦 **Package Manager Detection** - npm, yarn, pnpm, bun, pip, poetry, pipenv, uv
- 🎨 **Beautiful CLI** - Rich terminal output with progress bars and spinners
- 🛡️ **Error Handling** - Clear error messages with actionable solutions
- 🔄 **CI/CD Ready** - Perfect for automated deployments

## 🚀 Quick Start

### Installation

```bash
# Install with uv (recommended)
uv add deployx

# Or with pip
pip install deployx
```

### First Deployment

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

That's it! Your project is now live. 🎉

## 📚 Command Reference

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
- `--help` - Show help message

**Examples:**
```bash
deployx deploy                  # Interactive deployment
deployx deploy --force          # Skip confirmations (CI/CD)
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
  token_env: "GITHUB_TOKEN"      # Environment variable for token
```

**Setup:**
1. Create a [GitHub Personal Access Token](https://github.com/settings/tokens)
2. Grant `repo` and `workflow` permissions
3. Set environment variable: `export GITHUB_TOKEN=your_token_here`

## 🎯 Supported Projects

### JavaScript/Node.js
- **React** - Create React App, Vite
- **Vue.js** - Vue CLI, Vite
- **Next.js** - Static export
- **Angular** - Angular CLI
- **Express** - Node.js backend
- **Static HTML** - Plain HTML/CSS/JS

### Python
- **Django** - Web framework with static files
- **Flask** - Micro web framework
- **FastAPI** - Modern API framework

### Package Managers
- **Node.js**: npm, yarn, pnpm, bun
- **Python**: pip, poetry, pipenv, uv

## 🔧 Environment Setup

### GitHub Pages Setup

1. **Create Personal Access Token**
   - Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
   - Click "Generate new token (classic)"
   - Select scopes: `repo`, `workflow`
   - Copy the token

2. **Set Environment Variable**
   ```bash
   # Linux/macOS
   export GITHUB_TOKEN=your_token_here
   
   # Windows
   set GITHUB_TOKEN=your_token_here
   
   # Or add to your shell profile (.bashrc, .zshrc, etc.)
   echo 'export GITHUB_TOKEN=your_token_here' >> ~/.bashrc
   ```

3. **Repository Setup**
   - Repository must exist on GitHub
   - You need write access to the repository
   - Enable GitHub Pages in repository settings (optional - DeployX can enable it)

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
