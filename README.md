# 🚀 DeployX

One CLI for all your deployments  

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

DeployX eliminates the complexity of platform-specific deployment commands. Whether you're deploying a React app to Vercel, a static site to GitHub Pages, or a full-stack application to Railway, DeployX provides a unified interface that auto-detects your project type, configures build settings, and handles authentication—all through a single, intuitive command.

No more memorizing different CLI tools, configuration formats, or deployment workflows. Just run `deployx deploy` and watch your project go live.

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

#### Option 2: Step-by-step

1. **Navigate to your project directory**
   ```bash
   cd my-awesome-project
   ```

2. **Initialize deployment configuration**
   ```bash
   deployx init
   ```

3. **Deploy your project**
   ```bash
   deployx deploy
   ```

4. **Check deployment status**
   ```bash
   deployx status
   ```

That's it! Your project is now live. 🎉

### Additional Commands

**Preview before deploying:**
```bash
deployx deploy --dry-run        # See what would happen before actually deploying
```

**Manage configuration:**
```bash
deployx config show             # View current config
deployx config validate         # Check config is valid
```

## 📚 Commands

```bash
# Setup and deploy in one go
deployx interactive

# Initialize configuration
deployx init

# Deploy your project
deployx deploy
deployx deploy --dry-run        # Preview without deploying
deployx deploy --force          # Skip confirmations

# Check status and logs
deployx status
deployx logs --follow

# Manage configuration
deployx config show
deployx config edit

# View deployment history
deployx history --limit 10
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
```

Other platforms (Vercel, Netlify, Railway, Render) use similar simple configurations.

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

## 🙏 Acknowledgments

- Built with [Click](https://click.palletsprojects.com/) for CLI framework
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- [PyGithub](https://pygithub.readthedocs.io/) for GitHub API integration

---

Made with ❤️ by the DeployX team
