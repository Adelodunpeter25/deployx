#!/bin/bash
# DeployX Installation Script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${CYAN}"
cat << "EOF"
██████╗ ███████╗██████╗ ██╗      ██████╗ ██╗   ██╗██╗  ██╗
██╔══██╗██╔════╝██╔══██╗██║     ██╔═══██╗╚██╗ ██╔╝╚██╗██╔╝
██║  ██║█████╗  ██████╔╝██║     ██║   ██║ ╚████╔╝  ╚███╔╝ 
██║  ██║██╔══╝  ██╔═══╝ ██║     ██║   ██║  ╚██╔╝   ██╔██╗ 
██████╔╝███████╗██║     ███████╗╚██████╔╝   ██║   ██╔╝ ██╗
╚═════╝ ╚══════╝╚═╝     ╚══════╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝
EOF
echo -e "${NC}"
echo -e "${BLUE}One CLI for all your deployments${NC}"
echo ""

# Check if Python 3.9+ is installed
echo -e "${CYAN}[1/4]${NC} Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    echo -e "${YELLOW}💡 Install Python 3.9+ from https://python.org${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}❌ Python $REQUIRED_VERSION+ required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"

# Check if pip is installed
echo -e "${CYAN}[2/4]${NC} Checking pip installation..."
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 is not installed${NC}"
    echo -e "${YELLOW}💡 Install pip: python3 -m ensurepip${NC}"
    exit 1
fi
echo -e "${GREEN}✓ pip3 available${NC}"

# Install DeployX
echo -e "${CYAN}[3/4]${NC} Installing DeployX..."
if pip3 install --user deployx --quiet; then
    echo -e "${GREEN}✓ DeployX installed${NC}"
else
    echo -e "${RED}❌ Installation failed${NC}"
    exit 1
fi

# Verify installation
echo -e "${CYAN}[4/4]${NC} Verifying installation..."
if command -v deployx &> /dev/null; then
    echo -e "${GREEN}✓ DeployX is ready${NC}"
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ Installation successful!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${CYAN}🚀 Get started:${NC}"
    echo -e "   ${YELLOW}cd your-project${NC}"
    echo -e "   ${YELLOW}deployx init${NC}"
    echo -e "   ${YELLOW}deployx deploy${NC}"
    echo ""
    echo -e "${CYAN}📚 Documentation:${NC} https://github.com/Adelodunpeter25/deployx"
    echo ""
else
    echo -e "${YELLOW}⚠️  DeployX installed but not in PATH${NC}"
    echo ""
    echo -e "${CYAN}Add to your shell config (~/.bashrc or ~/.zshrc):${NC}"
    echo -e "   ${YELLOW}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
    echo ""
    echo -e "${CYAN}Then reload:${NC}"
    echo -e "   ${YELLOW}source ~/.bashrc${NC}  ${BLUE}# or source ~/.zshrc${NC}"
    echo ""
fi
