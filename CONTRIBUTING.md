# Contributing to DeployX

Thank you for your interest in contributing to DeployX! This guide will help you get started with contributing to the project.

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git
- GitHub account

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/Adelodunpeter25/deployx.git
   cd deployx
   ```

2. **Install dependencies**
   ```bash
   uv sync
   ```

3. **Verify installation**
   ```bash
   uv run python -m deployx --version
   ```
## 🏗️ Architecture

### Project Structure

```
deployx/
├── commands/           # CLI command implementations
│   ├── init.py        # Initialize configuration
│   ├── deploy.py      # Deploy projects
│   └── status.py      # Check deployment status
├── platforms/         # Platform integrations
│   ├── base.py        # Abstract base class
│   ├── github.py      # GitHub Pages
│   └── factory.py     # Platform factory
├── detectors/         # Project type detection
│   └── project.py     # Framework detection logic
├── utils/             # Utility modules
│   ├── config.py      # Configuration management
│   ├── ui.py          # Terminal UI helpers
│   ├── errors.py      # Error handling
│   └── validator.py   # Configuration validation
├── tests/             # Test suite
└── main.py           # CLI entry point
```

### Key Components

1. **Commands**: CLI command implementations using Click
2. **Platforms**: Deployment platform integrations
3. **Detectors**: Auto-detection of project types and frameworks
4. **Utils**: Shared utilities for config, UI, and error handling

## 🎨 Code Style

### Python Style Guidelines

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions focused and small (< 50 lines when possible)
- Use descriptive variable and function names

## ✨ Feature Requests

When requesting features:

1. **Describe the problem** the feature would solve
2. **Explain the proposed solution** in detail
3. **Consider alternatives** and explain why your solution is best
4. **Provide examples** of how the feature would be used
5. **Consider implementation complexity** and breaking changes

## 📝 Documentation

### Writing Documentation

- Use clear, concise language
- Include code examples for all features
- Add screenshots for UI-related features
- Keep examples up-to-date with current API
- Test all code examples before submitting

## 🔄 Pull Request Process

### Before Submitting

1. **Create an issue** to discuss major changes
2. **Fork the repository** and create a feature branch
3. **Write tests** for new functionality
4. **Update documentation** as needed
5. **Run the full test suite** and ensure all tests pass
6. **Follow code style guidelines**

## 🙏 Recognition

Contributors are recognized in:
- README.md contributors section
- GitHub contributors page

Thank you for contributing to DeployX! 🚀