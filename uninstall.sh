#!/bin/bash
# DeployX Uninstallation Script

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
echo -e "${BLUE}Uninstalling DeployX${NC}"
echo ""

# Check if pip is installed
echo -e "${CYAN}[1/3]${NC} Checking pip..."
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}❌ pip3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ pip3 available${NC}"

# Check if DeployX is installed
echo -e "${CYAN}[2/3]${NC} Checking DeployX installation..."
if ! pip3 show deployx &> /dev/null; then
    echo -e "${YELLOW}⚠️  DeployX is not installed${NC}"
    exit 0
fi
echo -e "${GREEN}✓ DeployX found${NC}"

# Uninstall DeployX
echo -e "${CYAN}[3/3]${NC} Removing DeployX..."
if pip3 uninstall -y deployx --quiet; then
    echo -e "${GREEN}✓ DeployX removed${NC}"
else
    echo -e "${RED}❌ Uninstallation failed${NC}"
    exit 1
fi

# Verify uninstallation
if ! pip3 show deployx &> /dev/null; then
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ DeployX uninstalled successfully!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${CYAN}💡 Note:${NC} Project configurations ${YELLOW}(deployx.yml)${NC} were not removed."
    echo -e "   Delete them manually if needed."
    echo ""
else
    echo -e "${RED}❌ Failed to uninstall DeployX${NC}"
    exit 1
fi
